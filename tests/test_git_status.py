import os
from pathlib import Path
import pty
import select
import shutil
import signal
import subprocess
import tempfile
import time
import unittest


REPOSITORY = Path(__file__).resolve().parents[1]
SCRIPT = REPOSITORY / "home/zsh/git-status.zsh"
ZSH = shutil.which("zsh")
GIT = shutil.which("git")
STARSHIP = shutil.which("starship")


@unittest.skipUnless(ZSH and GIT, "requires Zsh and Git")
class GitStatusTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="prompt-git-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.repo = self.root / "repo with spaces"
        self.repo.mkdir()
        self.env = os.environ | {
            "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
            "HOME": str(self.root), "ZDOTDIR": str(self.root),
            "TERM": "xterm-256color", "STARSHIP_CONFIG": str(REPOSITORY / "home/starship.toml"),
            "STARSHIP_CACHE": str(self.root / "starship"),
        }
        for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
            self.env.pop(name, None)
        self.git("init", "-q", "-b", "main")
        (self.repo / "tracked").write_text("base\n")
        self.git("add", "tracked")
        self.git("commit", "-qm", "initial")

    def git(self, *args, check=True):
        return subprocess.run(
            [GIT, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
             "-c", "commit.gpgsign=false", *args],
            cwd=self.repo, env=self.env, text=True, capture_output=True, check=check,
        )

    def scan(self, directory=None):
        result = subprocess.run(
            [ZSH, "-dfc", 'source "$1"; _dotfiles_git_status_scan "$2"',
             "scan", str(SCRIPT), str(directory or self.repo)],
            env=self.env, text=True, capture_output=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        return result.stdout.strip()


class GitStatusTests(GitStatusTestCase):
    def test_clean_untracked_staged_modified_deleted_priority(self):
        self.assertEqual(self.scan(), "0")
        (self.repo / "new").write_text("new\n")
        self.assertEqual(self.scan(), "34")
        self.git("add", "new")
        self.assertEqual(self.scan(), "32")
        (self.repo / "tracked").write_text("changed\n")
        self.assertEqual(self.scan(), "33")
        (self.repo / "tracked").unlink()
        self.assertEqual(self.scan(), "31")

    def test_rename_and_conflict(self):
        self.git("mv", "tracked", "renamed")
        self.assertEqual(self.scan(), "36")
        self.git("commit", "-qm", "rename")
        self.git("checkout", "-qb", "other")
        (self.repo / "renamed").write_text("other\n")
        self.git("commit", "-qam", "other change")
        self.git("checkout", "-q", "main")
        (self.repo / "renamed").write_text("main\n")
        self.git("commit", "-qam", "main change")
        self.assertEqual(self.git("merge", "other", check=False).returncode, 1)
        self.assertEqual(self.scan(), "35")

    def test_outside_repository_reports_unknown_without_errors(self):
        self.assertEqual(self.scan(self.root), "-")


@unittest.skipUnless(ZSH and GIT and STARSHIP, "requires Zsh, Git and Starship")
class AsyncGitStatusTests(GitStatusTestCase):
    def setUp(self):
        super().setUp()
        self.results = self.root / "results"
        self.calls = self.root / "calls"
        self.prompts = self.root / "prompts"
        self.bin = self.root / "bin"
        self.bin.mkdir()
        # Only status is slow; Starship still sees a real repository/worktree.
        wrapper = self.bin / "git"
        wrapper.write_text('''#!/bin/sh
if [ "$1" = --no-optional-locks ] && [ "$4" = status ]; then
  printf '%s\\n' "$$" >> "$TEST_CALLS"
  delay=0
  [ ! -f "$3/delay" ] || read -r delay < "$3/delay"
  sleep "$delay"
  [ ! -f "$3/status" ] || cat "$3/status"
  [ ! -f "$3/fail" ]
else
  exec "$TEST_REAL_GIT" "$@"
fi
''')
        wrapper.chmod(0o755)
        self.env.update({
            "PATH": str(self.bin) + os.pathsep + os.environ["PATH"],
            "TEST_REAL_GIT": GIT, "TEST_CALLS": str(self.calls),
            "TEST_RESULTS": str(self.results), "TEST_PROMPTS": str(self.prompts),
            "TEST_STARSHIP": STARSHIP, "TEST_SCRIPT": str(SCRIPT),
        })
        (self.root / ".zshrc").write_text('''
unsetopt bgnice
HISTFILE=/dev/null
SAVEHIST=0
eval "$("$TEST_STARSHIP" init zsh)"
source "$TEST_SCRIPT"
_test_status_ready() {
  _dotfiles_git_status_ready "$@"
  print -r -- "${STARSHIP_CMD_STATUS:-0}|$DOTFILES_GIT_STATUS" >> "$TEST_RESULTS"
}
zle -N _dotfiles_git_status_ready _test_status_ready
_test_prompt() { print -r -- prompt >> "$TEST_PROMPTS"; }
add-zsh-hook precmd _test_prompt
PROMPT='__PROMPT__ '$PROMPT
''')

    def terminal(self):
        self.start = time.monotonic()
        pid, fd = pty.fork()
        if pid == 0:
            os.chdir(self.repo)
            os.execve(ZSH, [ZSH, "-d", "-i"], self.env)
        self.output = b""

        def cleanup():
            # Normal exit exercises the worker cleanup hook.
            os.write(fd, b"\x03exit\n")
            for _ in range(100):
                if os.waitpid(pid, os.WNOHANG)[0]:
                    break
                time.sleep(0.01)
            else:
                os.kill(pid, signal.SIGKILL)
                os.waitpid(pid, 0)
            os.close(fd)

        self.addCleanup(cleanup)
        return fd

    def wait_for(self, fd, predicate):
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            if predicate():
                return
            if select.select([fd], [], [], 0.02)[0]:
                self.output += os.read(fd, 65536)
        self.fail(f"Timed out: {self.output!r}; results: {self.lines(self.results)}")

    @staticmethod
    def lines(path):
        return path.read_text().splitlines() if path.exists() else []

    def test_slow_scan_never_blocks_prompt_and_preserves_typed_input(self):
        (self.repo / "delay").write_text("2\n")
        (self.repo / "status").write_text(" M tracked\n")
        fd = self.terminal()
        self.wait_for(fd, lambda: b"__PROMPT__" in self.output)
        self.assertLess(time.monotonic() - self.start, 1)
        self.assertFalse(self.lines(self.results))
        os.write(fd, b"echo buffered-input")
        self.wait_for(fd, lambda: any("\x1b[1;33m" in x for x in self.lines(self.results)))
        self.assertEqual(len(self.lines(self.prompts)), 1, "redraw must not rerun precmd")
        os.write(fd, b"\n")
        self.wait_for(fd, lambda: b"\r\nbuffered-input\r\n" in self.output)
        self.assertNotIn(b"timed out", self.output)
        self.assertNotIn(b"[WARN]", self.output)
        self.assertNotIn(b"terminated", self.output)

    def test_directory_change_cancels_old_worker_and_uses_correct_worktree(self):
        other = self.root / "other worktree"
        self.git("worktree", "add", "-qb", "other", str(other))
        (self.repo / "delay").write_text("3\n")
        (self.repo / "status").write_text(" D tracked\n")
        (other / "status").write_text("?? untracked\n")
        self.env["TEST_OTHER"] = str(other)
        fd = self.terminal()
        self.wait_for(fd, lambda: bool(self.lines(self.calls)))
        old_pid = int(self.lines(self.calls)[0])
        os.write(fd, b'cd "$TEST_OTHER"\n')
        self.wait_for(fd, lambda: any("\x1b[1;34m" in x for x in self.lines(self.results)))
        self.assertFalse(any("\x1b[1;31m" in x for x in self.lines(self.results)))
        self.wait_for(fd, lambda: not self.process_exists(old_pid))
        self.assertNotIn(b"[WARN]", self.output)
        self.assertNotIn(b"terminated", self.output)

    @staticmethod
    def process_exists(pid):
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False

    def test_refresh_preserves_exit_status_and_clears_failed_result(self):
        (self.repo / "delay").write_text("0.2\n")
        (self.repo / "status").write_text(" M tracked\n")
        fd = self.terminal()
        self.wait_for(fd, lambda: b"__PROMPT__" in self.output)
        os.write(fd, b"false\n")
        self.wait_for(fd, lambda: any(x.startswith("1|\x1b[1;33m") for x in self.lines(self.results)))
        (self.repo / "fail").touch()
        os.write(fd, b":\n")
        self.wait_for(fd, lambda: bool(self.lines(self.results)) and self.lines(self.results)[-1] == "0|")
        self.assertNotIn(b"[WARN]", self.output)


if __name__ == "__main__":
    unittest.main()
