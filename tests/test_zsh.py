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
ZSH = shutil.which("zsh")


@unittest.skipUnless(ZSH, "requires Zsh")
class ZshTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="dotfiles-zsh-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.home = self.root / "home"
        self.home.mkdir()
        self.config = self.root / "checkout with spaces"
        self.config.mkdir()
        shutil.copy2(REPOSITORY / "home/.zshrc", self.config / ".zshrc")
        shutil.copytree(REPOSITORY / "home/zsh", self.config / "zsh")
        (self.home / ".zshrc").symlink_to(self.config / ".zshrc")
        binary = self.root / "bin"
        binary.mkdir()
        # Stub optional tools so no installed runtime or personal config is used.
        for name, initialization in {
            "starship": "startup_events+=(prompt)",
            "atuin": "startup_events+=(atuin); bindkey '^R' beginning-of-line; "
                     "bindkey '^[[A' beginning-of-line",
            "eza": "", "fd": "", "zoxide": "",
        }.items():
            executable = binary / name
            executable.write_text("#!/bin/sh\ncat <<'INIT'\n" + initialization + "\nINIT\n")
            executable.chmod(0o755)
        self.data = self.home / "local data"
        for plugin, event in (("zsh-autosuggestions", "autosuggestions"),
                              ("zsh-syntax-highlighting", "highlighting")):
            directory = self.data / "zsh/plugins" / plugin
            directory.mkdir(parents=True)
            (directory / f"{plugin}.zsh").write_text(f"startup_events+=({event})\n")
        self.environment = {
            "HOME": str(self.home), "ZDOTDIR": str(self.home),
            "PATH": str(binary) + os.pathsep + os.defpath,
            "TERM": "xterm-256color", "XDG_DATA_HOME": str(self.data),
            "XDG_CACHE_HOME": str(self.home / "cache"),
        }

    def startup(self):
        result = subprocess.run(
            [ZSH, "-d", "-f", "-i", "-c",
             'typeset -ga startup_events=(); source "$HOME/.zshrc"; '
             'print -r -- "events=${(j:,:)startup_events}"; '
             'print -r -- "early=${TEST_EARLY:-unset}"; '
             'alias ls; bindkey "^R"; bindkey "^[[A"'],
            cwd=self.root, env=self.environment, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        return result.stdout

    def assert_local_bindings(self, output):
        self.assertIn("ls='ls -lh'", output)
        self.assertIn('"^R" beginning-of-line', output)
        self.assertIn('"^[[A" beginning-of-line', output)


class ZshOverrideTests(ZshTestCase):
    def test_legacy_overrides_run_once_after_shared_setup_before_highlighting(self):
        (self.home / ".zshrc_local").write_text(
            "startup_events+=(legacy)\n"
            "alias ls='ls -lh'\n"
            'eval "$(atuin init zsh)"\n'
        )
        output = self.startup()
        self.assertIn("events=prompt,autosuggestions,legacy,atuin,highlighting", output)
        self.assert_local_bindings(output)

    def test_module_local_setup_runs_early_and_late_before_highlighting(self):
        (self.config / ".zshrc.local").write_text(
            "startup_events+=(early)\n"
            "export TEST_EARLY=ready\n"
            'ZSH_PLUGIN_DIRS=("$XDG_DATA_HOME/zsh/plugins")\n'
            "zshrc_local_after_init() {\n"
            " startup_events+=(late)\n"
            " alias ls='ls -lh'\n"
            ' eval "$(atuin init zsh)"\n'
            "}\n"
        )
        output = self.startup()
        self.assertIn("events=early,prompt,autosuggestions,late,atuin,highlighting", output)
        self.assertIn("early=ready", output)
        self.assert_local_bindings(output)

    def test_module_local_file_takes_precedence_over_legacy_file(self):
        (self.config / ".zshrc.local").write_text("startup_events+=(early)\n")
        (self.home / ".zshrc_local").write_text("startup_events+=(legacy)\n")
        output = self.startup()
        self.assertIn("events=early,prompt,autosuggestions,highlighting", output)
        self.assertNotIn("legacy", output)


@unittest.skipUnless(ZSH, "requires Zsh")
class ZshDeferredTests(ZshTestCase):
    def setUp(self):
        super().setUp()
        self.log = self.root / "events"
        self.environment["TEST_LOG"] = str(self.log)
        tool_bin = self.root / "selected tools"
        tool_bin.mkdir()
        tool = tool_bin / "selected-tool"
        tool.write_text('#!/bin/sh\nprintf "tool-ran\\n" >> "$TEST_LOG"\n')
        tool.chmod(0o755)
        self.environment["TEST_TOOL_BIN"] = str(tool_bin)
        self.local = self.config / ".zshrc.local"
        self.local.write_text('''
typeset -ga startup_events=()
PROMPT='__TEST_PROMPT__ '
RPROMPT=''
zshrc_local_after_init() {
  autoload -Uz add-zsh-hook add-zle-hook-widget
  _test_prompt() { print -r -- prompt >> "$TEST_LOG"; }
  _test_finish() { print -r -- existing-finish >> "$TEST_LOG"; }
  add-zsh-hook precmd _test_prompt
  add-zle-hook-widget line-finish _test_finish
}
zshrc_local_deferred_init() {
  print -r -- "init:${WIDGET:-eager}" >> "$TEST_LOG"
  path=("$TEST_TOOL_BIN" $path)
  _test_preexec() { print -r -- "history:$1" >> "$TEST_LOG"; }
  _test_addhistory() { print -r -- "added:${1%$'\\n'}" >> "$TEST_LOG"; }
  _test_search() { print -r -- search >> "$TEST_LOG"; }
  add-zsh-hook preexec _test_preexec
  add-zsh-hook zshaddhistory _test_addhistory
  zle -N _test_search
  bindkey '^R' _test_search
  print -r -- initialized >> "$TEST_LOG"
}
''')

    def terminal(self):
        pid, fd = pty.fork()
        if pid == 0:
            os.chdir(self.root)
            os.execve(ZSH, [ZSH, "-d", "-i"], self.environment)
        self.output = b""

        def cleanup():
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            os.waitpid(pid, 0)
            os.close(fd)

        self.addCleanup(cleanup)
        return fd

    def wait_for(self, fd, predicate):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if predicate():
                return
            readable, _, _ = select.select([fd], [], [], 0.02)
            if readable:
                try:
                    self.output += os.read(fd, 65536)
                except OSError:
                    break
        self.fail(f"Terminal timed out: {self.output!r}; events: {self.events()}")

    def events(self):
        return self.log.read_text().splitlines() if self.log.exists() else []

    def test_idle_initialization_runs_once_after_prompt_and_binds_history(self):
        fd = self.terminal()
        self.wait_for(fd, lambda: "initialized" in self.events())
        events = self.events()
        self.assertLess(events.index("prompt"), events.index("init:_dotfiles_init_idle"))
        os.write(fd, b"\x12")
        self.wait_for(fd, lambda: "search" in self.events())
        os.write(fd, b"selected-tool\n")
        self.wait_for(fd, lambda: "tool-ran" in self.events())
        events = self.events()
        self.assertEqual(events.count("initialized"), 1)
        self.assertIn("existing-finish", events)
        self.assertIn("history:selected-tool", events)
        self.assertIn("added:selected-tool", events)
        self.assertLess(events.index("initialized"), events.index("tool-ran"))

    def test_queued_first_command_initializes_before_history_and_execution(self):
        fd = self.terminal()
        # Queue a paste while the shell is still loading its startup files.
        os.write(fd, b"selected-tool\n")
        self.wait_for(fd, lambda: "tool-ran" in self.events())
        events = self.events()
        self.assertIn("init:_dotfiles_finish_init", events)
        self.assertEqual(events.count("initialized"), 1)
        self.assertEqual(events.count("history:selected-tool"), 1)
        self.assertEqual(events.count("added:selected-tool"), 1)
        self.assertLess(events.index("initialized"), events.index("history:selected-tool"))

    def test_opt_out_initializes_before_first_prompt(self):
        self.environment["DOTFILES_FAST_PROMPT"] = "1"
        self.environment["DOTFILES_DEFER_INIT"] = "0"
        fd = self.terminal()
        self.wait_for(fd, lambda: "prompt" in self.events())
        events = self.events()
        self.assertLess(events.index("initialized"), events.index("prompt"))

    def test_without_terminal_initializes_immediately(self):
        self.environment["DOTFILES_FAST_PROMPT"] = "1"
        self.startup()
        self.assertIn("initialized", self.events())

    def test_fast_prompt_appears_before_integrations(self):
        self.environment["DOTFILES_FAST_PROMPT"] = "1"
        text = self.local.read_text().replace(
            '  print -r -- "init:${WIDGET:-eager}"',
            '  print -r -- __INITIALIZING__\n  print -r -- "init:${WIDGET:-eager}"',
        )
        self.local.write_text(text)
        fd = self.terminal()
        self.wait_for(fd, lambda: b"__INITIALIZING__" in self.output)
        self.assertLess(self.output.index("╰─".encode()), self.output.index(b"__INITIALIZING__"))
        self.wait_for(fd, lambda: "initialized" in self.events())
        self.assertEqual(self.events().count("initialized"), 1)

    def test_fast_prompt_preserves_first_command_aliases_and_history(self):
        self.environment["DOTFILES_FAST_PROMPT"] = "1"
        text = self.local.read_text().replace(
            'zshrc_local_after_init() {',
            "zshrc_local_after_init() {\n  alias first-tool=selected-tool",
        )
        self.local.write_text(text)
        fd = self.terminal()
        os.write(fd, b"first-tool\n")
        self.wait_for(fd, lambda: "tool-ran" in self.events())
        events = self.events()
        self.assertIn("init:_dotfiles_finish_init", events)
        self.assertEqual(events.count("history:first-tool"), 1, events)
        self.assertEqual(events.count("added:first-tool"), 1, events)

    def test_fast_prompt_first_ctrl_r_initializes_and_dispatches_search(self):
        self.environment["DOTFILES_FAST_PROMPT"] = "1"
        fd = self.terminal()
        # Before ZLE starts, the tty can consume Ctrl-R as its reprint key.
        self.wait_for(fd, lambda: "╰─".encode() in self.output)
        os.write(fd, b"\x12")
        self.wait_for(fd, lambda: "search" in self.events())
        events = self.events()
        self.assertEqual(events.count("initialized"), 1)
        self.assertLess(events.index("initialized"), events.index("search"))

    def test_fast_prompt_first_tab_initializes_completion(self):
        self.environment["DOTFILES_FAST_PROMPT"] = "1"
        text = self.local.read_text().replace(
            '  bindkey \'^R\' _test_search',
            "  bindkey '^R' _test_search\n"
            "  _test_complete() { print -r -- completion >> \"$TEST_LOG\"; }\n"
            "  zle -N _test_complete\n  bindkey '^I' _test_complete",
        )
        self.local.write_text(text)
        fd = self.terminal()
        os.write(fd, b"\t")
        self.wait_for(fd, lambda: "completion" in self.events())
        events = self.events()
        self.assertEqual(events.count("initialized"), 1)
        self.assertLess(events.index("initialized"), events.index("completion"))


if __name__ == "__main__":
    unittest.main()
