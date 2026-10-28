import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


REPOSITORY = Path(__file__).resolve().parents[1]
ZSH = shutil.which("zsh")


@unittest.skipUnless(ZSH, "requires Zsh")
class ZshOverrideTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
