import errno
import os
from pathlib import Path
import select
import shutil
import signal
import stat
import subprocess
import tarfile
import tempfile
import time
import unittest


REPOSITORY = Path(__file__).resolve().parents[1]
GENERATED = (
    "node_modules", "build", "dist", "out", "tmp", "temp", ".cache", ".next",
    ".nuxt", "coverage", ".vite", ".turbo", ".vercel",
)


class DirectoryToolTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="dotfiles-directory-tools-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "source [x],&"
        self.source.mkdir()
        (self.source / "keep.txt").write_text("important contents\n")
        self.home = self.root / "home"
        self.home.mkdir()
        self.destination = self.root / "backups"
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.environment = os.environ | {"HOME": str(self.home)}

    def run_tool(self, name, *arguments, cwd=None, environment=None):
        return subprocess.run(
            ["bash", str(REPOSITORY / "scripts" / f"{name}.sh"), *map(str, arguments)],
            cwd=cwd or self.root, env=self.environment | (environment or {}),
            text=True, capture_output=True, timeout=20,
        )

    def command_stub(self, name, body):
        command = self.bin / name
        command.write_text("#!/bin/sh\n" + body)
        command.chmod(0o755)
        return {"PATH": str(self.bin) + os.pathsep + os.environ["PATH"]}

    def test_backup_resolves_source_alias_and_preserves_internal_symlinks(self):
        alias = self.root / "source alias"
        alias.symlink_to(self.source, target_is_directory=True)
        (self.source / "relative-link").symlink_to("./keep.txt")
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "private").write_text("outside the backup")
        (self.source / "outside-link").symlink_to(outside, target_is_directory=True)
        (self.source / ".hidden").write_text("hidden contents")

        result = self.run_tool("backup-dir", alias, self.destination)
        self.assertEqual(result.returncode, 0, result.stderr)
        archive, = self.destination.iterdir()
        self.assertEqual(stat.S_IMODE(archive.stat().st_mode), 0o600)
        with tarfile.open(archive) as backup:
            prefix = self.source.name + "/"
            self.assertEqual(backup.extractfile(prefix + "keep.txt").read(), b"important contents\n")
            self.assertEqual(backup.extractfile(prefix + ".hidden").read(), b"hidden contents")
            self.assertEqual(backup.getmember(prefix + "relative-link").linkname, "./keep.txt")
            self.assertTrue(backup.getmember(prefix + "outside-link").issym())
            self.assertNotIn(prefix + "outside-link/private", backup.getnames())

    def test_generated_exclusions_are_opt_in_and_preserve_source_data(self):
        generated_files = []
        for parent in (self.source, self.source / "nested project"):
            for name in GENERATED:
                directory = parent / name
                directory.mkdir(parents=True)
                payload = directory / "payload"
                payload.write_text("rebuildable")
                generated_files.append(payload)
        for destination, options in ((self.destination, ()), (self.root / "filtered", ("--exclude-generated",))):
            result = self.run_tool("backup-dir", *options, self.source, destination)
            self.assertEqual(result.returncode, 0, result.stderr)
            archive, = destination.iterdir()
            with tarfile.open(archive) as backup:
                members = backup.getnames()
                self.assertIn(self.source.name + "/keep.txt", members)
                for payload in generated_files:
                    member = str(payload.relative_to(self.source.parent))
                    if options:
                        self.assertNotIn(member, members)
                    else:
                        self.assertEqual(backup.extractfile(member).read(), b"rebuildable")
        for payload in generated_files:
            self.assertEqual(payload.read_text(), "rebuildable")

    def test_backup_rejects_destination_inside_source_even_through_alias(self):
        alias = self.root / "source alias"
        alias.symlink_to(self.source, target_is_directory=True)
        for destination in (self.source, self.source / "new/backups", alias / "new/backups"):
            with self.subTest(destination=destination):
                result = self.run_tool("backup-dir", self.source, destination)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("outside the source", result.stderr)
                self.assertFalse((self.source / "new").exists())
        self.assertEqual((self.source / "keep.txt").read_text(), "important contents\n")

    def test_backup_does_not_overwrite_same_timestamp_archive(self):
        environment = self.command_stub("date", "printf '2030_01_02_030405\\n'\n")
        first = self.run_tool("backup-dir", self.source, self.destination, environment=environment)
        self.assertEqual(first.returncode, 0, first.stderr)
        archive, = self.destination.iterdir()
        previous = archive.read_bytes()
        (self.source / "keep.txt").write_text("changed contents")
        second = self.run_tool("backup-dir", self.source, self.destination, environment=environment)
        self.assertNotEqual(second.returncode, 0)
        self.assertIn("already exists", second.stderr)
        self.assertEqual(archive.read_bytes(), previous)
        self.assertEqual(list(self.destination.iterdir()), [archive])

    def test_encryption_fails_closed_when_age_is_missing(self):
        (self.bin / "bash").symlink_to(shutil.which("bash"))
        result = self.run_tool(
            "backup-dir", "--encrypt", self.source, self.destination,
            environment={"PATH": str(self.bin)},
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("age is required", result.stderr)
        self.assertFalse(self.destination.exists())

    def test_pipeline_failures_leave_no_partial_or_plaintext_archives(self):
        for failing_command in ("tar", "age"):
            with self.subTest(failing_command=failing_command):
                for command in self.bin.iterdir():
                    command.unlink()
                environment = self.command_stub(failing_command, "cat >/dev/null\nprintf partial\nexit 9\n")
                if failing_command == "tar":
                    self.command_stub("tar", "printf partial\nexit 9\n")
                    self.command_stub("age", "cat\n")
                result = self.run_tool(
                    "backup-dir", "--encrypt", self.source, self.destination, environment=environment,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(list(self.destination.iterdir()), [])
                self.assertEqual((self.source / "keep.txt").read_text(), "important contents\n")

    def test_cleanup_requires_apply_and_preserves_nonmatches_and_symlinks(self):
        for command in ("clean-node-modules", "clean-generated"):
            with self.subTest(command=command):
                target = self.root / command
                target.mkdir()
                generated = []
                for name in GENERATED:
                    directory = target / "-project with\nnewline" / name
                    directory.mkdir(parents=True)
                    (directory / "payload").write_text("generated data")
                    generated.append(directory)
                nested = generated[0] / "dependency/node_modules"
                nested.mkdir(parents=True)
                outside = self.root / (command + "-outside")
                (outside / "node_modules").mkdir(parents=True)
                (outside / "node_modules/keep").write_text("outside data")
                (target / "linked-project").symlink_to(outside, target_is_directory=True)
                (target / "node_modules").symlink_to(outside, target_is_directory=True)
                (target / "build").write_text("not a generated directory")
                (target / "keep.txt").write_text("source data")

                preview = self.run_tool(command, cwd=target)
                self.assertEqual(preview.returncode, 0, preview.stderr)
                self.assertIn("node_modules", preview.stdout)
                for directory in generated:
                    self.assertTrue(directory.is_dir())
                applied = self.run_tool(command, "--apply", target)
                self.assertEqual(applied.returncode, 0, applied.stderr)
                for directory in generated:
                    removed = command == "clean-generated" or directory.name == "node_modules"
                    self.assertEqual(directory.exists(), not removed)
                self.assertEqual((target / "keep.txt").read_text(), "source data")
                self.assertEqual((target / "build").read_text(), "not a generated directory")
                self.assertTrue((target / "node_modules").is_symlink())
                self.assertTrue((target / "linked-project").is_symlink())
                self.assertEqual((outside / "node_modules/keep").read_text(), "outside data")

    def test_root_and_root_alias_are_rejected_before_traversal(self):
        alias = self.root / "root-alias"
        alias.symlink_to("/", target_is_directory=True)
        environment = self.command_stub("find", "echo 'unexpected traversal' >&2\nexit 99\n")
        self.command_stub("tar", "echo 'unexpected traversal' >&2\nexit 99\n")
        for command in ("backup-dir", "clean-node-modules", "clean-generated"):
            for target in (Path("/"), alias):
                with self.subTest(command=command, target=target):
                    result = self.run_tool(command, target, environment=environment)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("Refusing", result.stderr)
                    self.assertNotIn("unexpected traversal", result.stderr)

    def run_terminal(self, command, responses):
        import pty

        pid, terminal = pty.fork()
        if pid == 0:
            os.chdir(self.root)
            os.execvpe(command[0], list(map(str, command)), self.environment)
        transcript = b""
        pending = b""
        responses = iter(responses)
        response = next(responses, None)
        status = None
        deadline = time.monotonic() + 30
        try:
            while time.monotonic() < deadline:
                if select.select([terminal], [], [], 0.1)[0]:
                    try:
                        chunk = os.read(terminal, 65536)
                    except OSError as error:
                        if error.errno != errno.EIO:
                            raise
                        chunk = b""
                    transcript += chunk
                    pending += chunk
                    if response is not None and response[0] in pending:
                        pending = pending.partition(response[0])[2]
                        os.write(terminal, response[1])
                        response = next(responses, None)
                completed, child_status = os.waitpid(pid, os.WNOHANG)
                if completed:
                    status = child_status
                    break
            self.assertIsNotNone(status, transcript.decode(errors="replace"))
            return os.waitstatus_to_exitcode(status), transcript.decode(errors="replace")
        finally:
            if status is None:
                try:
                    os.killpg(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                os.waitpid(pid, 0)
            os.close(terminal)

    @unittest.skipUnless(shutil.which("age") and os.name == "posix", "requires age and a terminal")
    def test_real_age_passphrase_round_trip_and_wrong_password_rejection(self):
        passphrase = b"disposable backup test passphrase\n"
        status, output = self.run_terminal(
            ["bash", REPOSITORY / "scripts/backup-dir.sh", "--encrypt", self.source, self.destination],
            [(b"Enter passphrase (leave empty to autogenerate a secure one):", passphrase),
             (b"Confirm passphrase:", passphrase)],
        )
        self.assertEqual(status, 0, output)
        archive, = self.destination.iterdir()
        self.assertTrue(archive.name.endswith(".tar.gz.age"))
        self.assertEqual(stat.S_IMODE(archive.stat().st_mode), 0o600)
        self.assertTrue(archive.read_bytes().startswith(b"age-encryption.org/v1\n"))
        restored = self.root / "restored.tar.gz"
        status, output = self.run_terminal(
            ["age", "--decrypt", "--output", restored, archive],
            [(b"Enter passphrase:", passphrase)],
        )
        self.assertEqual(status, 0, output)
        with tarfile.open(restored) as backup:
            self.assertEqual(
                backup.extractfile(self.source.name + "/keep.txt").read(), b"important contents\n",
            )
        rejected = self.root / "rejected.tar.gz"
        status, output = self.run_terminal(
            ["age", "--decrypt", "--output", rejected, archive],
            [(b"Enter passphrase:", b"wrong test passphrase\n")],
        )
        self.assertNotEqual(status, 0, output)
        self.assertIn("incorrect passphrase", output)
        self.assertTrue(not rejected.exists() or rejected.stat().st_size == 0)


if __name__ == "__main__":
    unittest.main()
