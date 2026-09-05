import json
import os
from pathlib import Path
import select
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest


REPOSITORY = Path(__file__).resolve().parents[1]
GIT = shutil.which("git")
MODULES = ("alpha", "module with spaces", "gamma")

# Git's own recursive subprocesses must use the wrapper too, not just shell calls.
GIT_WRAPPER = r'''#!PYTHON
import json
import os
from pathlib import Path
import socket
import sys

arguments = sys.argv[1:]
directory = Path.cwd()
index = 0
while index < len(arguments):
    argument = arguments[index]
    if argument in ("-C", "-c", "--git-dir", "--work-tree"):
        if argument == "-C":
            directory = (directory / arguments[index + 1]).resolve()
        index += 2
    elif argument.startswith("-"):
        index += 1
    else:
        break
command = arguments[index] if index < len(arguments) else ""
root = Path(os.environ["UPDATE_ROOT"])
if command == "clone":
    directory = (directory / arguments[-1]).resolve()
module = next((name for name in json.loads(os.environ["UPDATE_MODULES"])
               if directory in (root / name, root / ".git" / "modules" / name)), None)
if module and command in ("pull", "fetch", "clone"):
    event = {"module": module, "command": command, "group": os.getpgrp()}
    with socket.create_connection(("127.0.0.1", int(os.environ["UPDATE_PORT"])), 15) as connection:
        connection.settimeout(15)
        connection.sendall(json.dumps(event).encode() + b"\n")
        if connection.recv(1) != b"G":
            raise SystemExit("sibling Git operations did not reach the barrier")
os.execv(os.environ["REAL_GIT"], [os.environ["REAL_GIT"], *arguments])
'''


@unittest.skipUnless(GIT and os.name == "posix", "requires Git and POSIX process groups")
class UpdateConcurrencyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        home = self.directory / "home"
        home.mkdir()
        (home / ".gitconfig").write_text(
            "[user]\n name = Update Test\n email = update@example.invalid\n"
            "[protocol \"file\"]\n allow = always\n"
            "[pull]\n rebase = false\n",
            encoding="utf-8",
        )
        self.environment = {
            key: value for key, value in os.environ.items()
            if not key.startswith("GIT_") and key not in ("DOTFILES_JOBS", "PARALLEL_JOBS")
        }
        self.environment.update(
            HOME=str(home),
            XDG_CONFIG_HOME=str(home / "config"),
            GIT_CONFIG_NOSYSTEM="1",
            GIT_TERMINAL_PROMPT="0",
        )
        self.origins = {}
        self.superproject = self.directory / "superproject"
        self.checkout = self.directory / "checkout"
        self.git(self.directory, "init", "-b", "main", str(self.superproject))
        for index, module in enumerate(MODULES):
            origin = self.directory / f"origin-{index}"
            self.git(self.directory, "init", "-b", "main", str(origin))
            (origin / "version").write_text("one\n", encoding="utf-8")
            self.commit(origin, "initial version")
            self.git(self.superproject, "submodule", "add", str(origin), module)
            self.origins[module] = origin
        self.commit(self.superproject, "initial submodules")
        self.git(self.directory, "clone", str(self.superproject), str(self.checkout))
        (self.checkout / "setup").mkdir()
        shutil.copy2(REPOSITORY / "update.sh", self.checkout / "update.sh")
        shutil.copy2(REPOSITORY / "setup/parallel.sh", self.checkout / "setup/parallel.sh")

    def git(self, directory, *arguments):
        result = subprocess.run(
            [GIT, *arguments], cwd=directory, env=self.environment,
            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        return result.stdout.strip()

    def commit(self, directory, message):
        self.git(directory, "add", "--all")
        self.git(directory, "commit", "-m", message)
        return self.git(directory, "rev-parse", "HEAD")

    def advance_origins(self):
        commits = {}
        for module, origin in self.origins.items():
            (origin / "version").write_text("two\n", encoding="utf-8")
            commits[module] = self.commit(origin, "new remote version")
            self.git(
                self.superproject, "update-index", "--cacheinfo",
                f"160000,{commits[module]},{module}",
            )
        # Do not add the old working-tree gitlinks over the newly staged pins.
        self.git(self.superproject, "commit", "-m", "advance submodule pins")
        return commits

    def run_update(self):
        executable_directory = self.directory / "bin"
        executable_directory.mkdir()
        wrapper = executable_directory / "git"
        wrapper.write_text(GIT_WRAPPER.replace("#!PYTHON", f"#!{sys.executable}"), encoding="utf-8")
        wrapper.chmod(0o755)
        git_exec_path = self.git(self.directory, "--exec-path")
        for helper in Path(git_exec_path).iterdir():
            if helper.name != "git":
                (executable_directory / helper.name).symlink_to(helper)
        environment = self.environment | {
            "PATH": os.pathsep.join((str(executable_directory), git_exec_path, self.environment["PATH"])),
            "GIT_EXEC_PATH": str(executable_directory),
            "REAL_GIT": GIT,
            "UPDATE_ROOT": str(self.checkout),
            "UPDATE_MODULES": json.dumps(MODULES),
            "GIT_CONFIG_COUNT": "2",
            "GIT_CONFIG_KEY_0": "submodule.recurse",
            "GIT_CONFIG_VALUE_0": "true",
            "GIT_CONFIG_KEY_1": "fetch.recurseSubmodules",
            "GIT_CONFIG_VALUE_1": "true",
        }
        events = []
        waiting = []
        arrived = set()
        with socket.socket() as listener, tempfile.TemporaryFile(mode="w+") as output:
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            environment["UPDATE_PORT"] = str(listener.getsockname()[1])
            process = subprocess.Popen(
                ["./update.sh"], cwd=self.checkout, env=environment,
                stdout=output, stderr=subprocess.STDOUT, start_new_session=True,
            )
            deadline = time.monotonic() + 25
            timed_out = False
            try:
                while process.poll() is None:
                    if time.monotonic() >= deadline:
                        timed_out = True
                        break
                    if not select.select([listener], [], [], 0.1)[0]:
                        continue
                    connection, _ = listener.accept()
                    connection.settimeout(5)
                    with connection.makefile("rb") as stream:
                        event = json.loads(stream.readline())
                    events.append(event)
                    if event["command"] == "pull" and event["module"] not in arrived:
                        arrived.add(event["module"])
                        waiting.append(connection)
                    else:
                        connection.sendall(b"G")
                        connection.close()
                    # No sibling can proceed until every sibling is inside its own pull.
                    if arrived == set(MODULES):
                        for connection in waiting:
                            connection.sendall(b"G")
                            connection.close()
                        waiting.clear()
            finally:
                for connection in waiting:
                    connection.close()
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        for group in {process.pid, *(event["group"] for event in events)}:
                            try:
                                os.killpg(group, signal.SIGKILL)
                            except ProcessLookupError:
                                pass
                        process.wait(timeout=5)
            output.seek(0)
            transcript = output.read()
        self.assertFalse(timed_out, f"sibling barrier timed out:\n{transcript}")
        self.assertEqual(arrived, set(MODULES), transcript)
        pulls = [event for event in events if event["command"] == "pull"]
        self.assertEqual(len({event["group"] for event in pulls}), len(MODULES), transcript)
        self.assertTrue(all(event["group"] != process.pid for event in events), transcript)
        return process.returncode, transcript

    def assert_updated(self, commits, modules=MODULES):
        for module in modules:
            directory = self.checkout / module
            self.assertEqual((directory / "version").read_text(encoding="utf-8"), "two\n")
            self.assertEqual(self.git(directory, "branch", "--show-current"), "main")
            self.git(directory, "merge-base", "--is-ancestor", commits[module], "HEAD")

    def test_changed_parent_pins_pull_siblings_concurrently_without_losing_local_commits(self):
        self.git(self.checkout, "submodule", "update", "--init", "--recursive")
        module = self.checkout / MODULES[0]
        self.git(module, "switch", "main")
        (module / "local-only").write_text("keep this commit\n", encoding="utf-8")
        local_commit = self.commit(module, "local committed work")
        commits = self.advance_origins()

        status, output = self.run_update()

        self.assertEqual(status, 0, output)
        self.assert_updated(commits)
        self.git(module, "merge-base", "--is-ancestor", local_commit, "HEAD")
        self.assertEqual((module / "local-only").read_text(encoding="utf-8"), "keep this commit\n")
        self.assertEqual(
            self.git(self.checkout, "rev-parse", "HEAD"),
            self.git(self.superproject, "rev-parse", "HEAD"),
        )

    def test_uninitialized_siblings_are_initialized_and_pulled_in_their_own_jobs(self):
        commits = self.advance_origins()

        status, output = self.run_update()

        self.assertEqual(status, 0, output)
        self.assert_updated(commits)

    def test_failed_pull_reports_module_and_preserves_successful_siblings(self):
        self.git(self.checkout, "submodule", "update", "--init", "--recursive")
        commits = self.advance_origins()
        failed_module = MODULES[1]
        failed_directory = self.checkout / failed_module
        original_commit = self.git(failed_directory, "rev-parse", "HEAD")
        self.git(failed_directory, "remote", "set-url", "origin", str(self.directory / "missing-origin"))

        status, output = self.run_update()

        self.assertEqual(status, 1, output)
        self.assertIn(failed_module, output)
        self.assertRegex(output, r"(?i)(failed[^\n]*module with spaces|module with spaces[^\n]*failed)")
        self.assert_updated(commits, (MODULES[0], MODULES[2]))
        self.assertEqual(self.git(failed_directory, "rev-parse", "HEAD"), original_commit)
        self.assertEqual((failed_directory / "version").read_text(encoding="utf-8"), "one\n")


if __name__ == "__main__":
    unittest.main()
