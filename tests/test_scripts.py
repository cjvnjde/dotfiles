import io
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tarfile
import tempfile
import unittest


REPOSITORY = Path(__file__).resolve().parents[1]


class PackageSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="dotfiles-packages-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.checkout = self.root / "checkout with spaces"
        self.home = self.root / "home"
        self.home.mkdir()
        (self.checkout / "scripts").mkdir(parents=True)
        self.script = self.checkout / "scripts/save-installed-packages.sh"
        shutil.copy2(REPOSITORY / "scripts/save-installed-packages.sh", self.script)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        pacman = self.bin / "pacman"
        pacman.write_text(
            '#!/bin/sh\n'
            'case "$1" in\n'
            '  -Qqen) printf "bash\\ngit\\n" ;;\n'
            '  -Qqem) [ "${FAIL_AUR:-0}" = 0 ] || exit 7; printf "paru-bin\\n" ;;\n'
            '  *) exit 2 ;;\n'
            'esac\n'
        )
        pacman.chmod(0o755)
        mise = self.bin / "mise"
        mise.write_text(
            '#!/bin/sh\n'
            '[ "${FAIL_MISE:-0}" = 0 ] || exit 8\n'
            'printf \'%s\\n\' \'{"node": [{"version": "26.13.0", "installed": true}]}\'\n'
        )
        mise.chmod(0o755)
        self.environment = dict(os.environ, HOME=str(self.home),
                                PATH=str(self.bin) + os.pathsep + os.defpath)

    def run_snapshot(self, *arguments, script=None, **environment):
        return subprocess.run(
            ["bash", str(script or self.script), *map(str, arguments)], cwd=self.root,
            env=self.environment | environment, text=True, capture_output=True, timeout=10,
        )

    def test_default_uses_system_state_directory_through_installed_link(self):
        first = self.bin / "save-installed-packages"
        first.symlink_to("../checkout with spaces/scripts/save-installed-packages.sh")
        second = self.root / "snapshot"
        second.symlink_to("bin/save-installed-packages")
        result = self.run_snapshot(script=second)
        self.assertEqual(result.returncode, 0, result.stderr)
        packages = self.home / ".local/state/system"
        self.assertEqual((packages / "official-packages.txt").read_text(), "bash\ngit\n")
        self.assertEqual((packages / "aur-packages.txt").read_text(), "paru-bin\n")
        self.assertFalse((self.root / "packages").exists())
        self.assertFalse((self.checkout / "packages").exists())

    def test_explicit_destination_creates_nested_directory(self):
        destination = self.root / "chosen folder/packages"
        result = self.run_snapshot(destination)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((destination / "official-packages.txt").read_text(), "bash\ngit\n")
        self.assertEqual((destination / "aur-packages.txt").read_text(), "paru-bin\n")
        self.assertFalse((self.checkout / "packages").exists())
        self.assertFalse((self.home / ".local/state/system").exists())

    def test_query_failures_preserve_all_existing_snapshots(self):
        destination = self.root / "existing"
        destination.mkdir()
        names = ("official-packages.txt", "aur-packages.txt", "mise-packages.json")
        for name in names:
            (destination / name).write_text("previous " + name)
        for failure in ("FAIL_AUR", "FAIL_MISE"):
            with self.subTest(failure=failure):
                result = self.run_snapshot(destination, **{failure: "1"})
                self.assertNotEqual(result.returncode, 0)
                for name in names:
                    self.assertEqual((destination / name).read_text(), "previous " + name)


@unittest.skipUnless(shutil.which("gpg") and shutil.which("gpgconf"), "requires GnuPG")
class GpgBackupTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="dotfiles-gpg-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.target = self.root / "target"
        for home in (self.source, self.target):
            home.mkdir(mode=0o700)
            self.addCleanup(subprocess.run, ["gpgconf", "--homedir", str(home), "--kill", "all"],
                            capture_output=True, timeout=10)
        self.gpg(self.source, "--batch", "--pinentry-mode", "loopback", "--passphrase", "",
                 "--quick-generate-key", "Dotfiles Test <test@example.invalid>", "ed25519", "sign", "0")
        listing = self.gpg(self.source, "--with-colons", "--list-secret-keys").stdout
        self.fingerprint = next(line.split(":")[9] for line in listing.splitlines()
                                if line.startswith("fpr:"))
        self.script = REPOSITORY / "scripts/backup-gpg.sh"

    def gpg(self, home, *arguments):
        return subprocess.run(
            ["gpg", "--homedir", str(home), *arguments], text=True,
            capture_output=True, check=True, timeout=20,
        )

    def run_backup(self, home, *arguments):
        return subprocess.run(
            ["bash", str(self.script), *map(str, arguments)],
            env=dict(os.environ, GNUPGHOME=str(home)), text=True,
            capture_output=True, timeout=20,
        )

    def test_plain_round_trip_restores_usable_secret_key_and_ownertrust(self):
        archive = self.root / "plain backup.tar.gz"
        result = self.run_backup(self.source, "--no-age", "backup", self.fingerprint, archive)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(stat.S_IMODE(archive.stat().st_mode), 0o600)
        result = self.run_backup(self.target, "--no-age", "restore", archive)
        self.assertEqual(result.returncode, 0, result.stderr)
        message = self.root / "message"
        message.write_text("restored key signs this message\n")
        self.gpg(self.target, "--batch", "--detach-sign", str(message))
        self.gpg(self.source, "--verify", str(message) + ".sig", str(message))
        self.assertIn(self.fingerprint + ":6:", self.gpg(self.target, "--export-ownertrust").stdout)

    def test_backup_never_overwrites_existing_output(self):
        archive = self.root / "existing"
        archive.write_bytes(b"keep this archive")
        result = self.run_backup(self.source, "--no-age", "backup", self.fingerprint, archive)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(archive.read_bytes(), b"keep this archive")

    def test_incomplete_archive_does_not_partially_import_keys(self):
        archive = self.root / "incomplete.tar.gz"
        public = subprocess.run(["gpg", "--homedir", str(self.source), "--export"],
                                capture_output=True, check=True, timeout=10).stdout
        with tarfile.open(archive, "w:gz") as bundle:
            member = tarfile.TarInfo("./pubkeys.gpg")
            member.size = len(public)
            bundle.addfile(member, io.BytesIO(public))
        result = self.run_backup(self.target, "--no-age", "restore", archive)
        self.assertNotEqual(result.returncode, 0)
        listing = self.gpg(self.target, "--with-colons", "--list-keys").stdout
        self.assertFalse(any(line.startswith("pub:") for line in listing.splitlines()))


if __name__ == "__main__":
    unittest.main()
