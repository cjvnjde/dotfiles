import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


REPOSITORY = Path(__file__).resolve().parents[1]


class LinkerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="dotfiles-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.checkout = self.root / "checkout with spaces"
        self.home = self.root / "home"
        self.checkout.mkdir()
        self.home.mkdir()
        (self.checkout / "setup").mkdir()
        for name in ("setup.sh", "setup/lib.sh", "setup/parallel.sh"):
            shutil.copy2(REPOSITORY / name, self.checkout / name)
        self.environment = {
            key: value for key, value in os.environ.items()
            if not key.startswith(("GIT_", "DOTFILES_"))
        } | {
            "HOME": str(self.home),
            "XDG_CONFIG_HOME": str(self.home / ".config"),
            "GIT_CONFIG_NOSYSTEM": "1",
        }

    def run_bash(self, script, *arguments, expected=0):
        result = subprocess.run(
            ["bash", "-euo", "pipefail", "-c", script, "test", *map(str, arguments)],
            cwd=self.checkout, env=self.environment, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=15,
        )
        self.assertEqual(result.returncode, expected, result.stdout)
        return result.stdout

    def add_module(self, name):
        directory = self.checkout / name
        directory.mkdir()
        (directory / "config").write_text("shared\n")
        (directory / "setup.sh").write_text(
            'source "$DOTFILES_DIR/setup/lib.sh"\n'
            f'source_path="$DOTFILES_DIR/{name}"\n'
            f'dest="$HOME/.config/{name}"\n'
            'case "$1" in\n'
            'enable) link_path "$source_path" "$dest" ;;\n'
            'disable) unlink_path "$source_path" "$dest" ;;\n'
            'esac\n'
        )
        return directory

    def test_directory_backup_restore_keeps_machine_files_and_latest_backup(self):
        source = self.add_module("editor")
        destination = self.home / ".config/editor"
        destination.mkdir(parents=True)
        (destination / "config").write_text("original\n")
        (destination / "private.local").write_text("machine settings\n")
        (self.checkout / ".modules").write_text("editor\n")
        self.run_bash('bash setup.sh editor')
        self.run_bash('bash setup.sh editor')
        self.assertEqual(destination.resolve(), source)
        self.assertFalse(Path(str(destination) + ".bak1").exists())
        self.run_bash('bash setup.sh --restore editor')
        self.assertFalse(destination.is_symlink())
        self.assertEqual((destination / "private.local").read_text(), "machine settings\n")

        # Numeric ordering must handle more than nine generations and gaps.
        for suffix in ("", "2", "9", "10"):
            Path(str(destination) + ".bak" + suffix).write_text(suffix or "first")
        self.run_bash('source setup/lib.sh; backup_path "$1"; restore_backup "$1"', destination)
        self.assertEqual(destination.read_text(), "10")
        self.assertTrue(Path(str(destination) + ".bak9").exists())

    def test_restore_never_overwrites_an_unmanaged_config_or_link(self):
        source = self.checkout / "source"
        source.write_text("shared")
        destination = self.home / "config"
        backup = Path(str(destination) + ".bak")
        destination.write_text("unrelated")
        backup.write_text("original")
        self.run_bash(
            'source setup/lib.sh; DOTFILES_RESTORE_BACKUPS=1; unlink_path "$1" "$2"',
            source, destination,
        )
        self.assertEqual(destination.read_text(), "unrelated")
        self.assertEqual(backup.read_text(), "original")
        self.run_bash('source setup/lib.sh; restore_backup "$1"', destination, expected=1)
        destination.unlink()
        destination.symlink_to(self.root / "missing unrelated target")
        self.run_bash(
            'source setup/lib.sh; DOTFILES_RESTORE_BACKUPS=1; unlink_path "$1" "$2"',
            source, destination,
        )
        self.assertTrue(destination.is_symlink())

    def test_restore_supports_broken_symlink_backups_and_missing_destination(self):
        destination = self.home / "config"
        backup = Path(str(destination) + ".bak")
        backup.symlink_to(self.root / "old missing target")
        self.run_bash('source setup/lib.sh; restore_backup "$1"', destination)
        self.assertTrue(destination.is_symlink())
        self.assertEqual(os.readlink(destination), str(self.root / "old missing target"))

    def test_dry_run_executes_no_modules_or_after_setup(self):
        module = self.add_module("editor")
        (module / "setup.sh").write_text('touch "$HOME/module-was-run"\n')
        (self.checkout / "after_setup.sh").write_text('touch "$HOME/after-was-run"\n')
        (self.checkout / ".modules").write_text("editor\n")
        output = self.run_bash('bash setup.sh --dry-run')
        self.assertIn("Would apply editor", output)
        self.assertEqual(list(self.home.iterdir()), [])
        self.run_bash('bash setup.sh --unknown', expected=2)
        self.run_bash('bash setup.sh missing-module', expected=2)

    def test_restore_without_names_only_visits_enabled_modules_and_skips_hooks(self):
        self.add_module("editor")
        disabled = self.add_module("disabled")
        (disabled / "setup.sh").write_text('touch "$HOME/disabled-was-run"\n')
        (self.checkout / ".modules").write_text("editor\n")
        self.run_bash('bash setup.sh editor')
        (self.checkout / "after_setup.sh").write_text('touch "$HOME/after-was-run"\n')
        self.run_bash('bash setup.sh --restore')
        self.assertFalse((self.home / "disabled-was-run").exists())
        self.assertFalse((self.home / "after-was-run").exists())
        self.assertFalse((self.home / ".config/editor").exists())

    def test_git_module_includes_private_file_and_restores_existing_config(self):
        (self.checkout / "home/setup").mkdir(parents=True)
        (self.checkout / "home/git").mkdir()
        shutil.copy2(REPOSITORY / "home/setup/git.sh", self.checkout / "home/setup/git.sh")
        shutil.copy2(REPOSITORY / "home/git/config", self.checkout / "home/git/config")
        (self.checkout / "home/git/config.local").write_text('[user]\n name = Private Machine\n')
        destination = self.home / ".config/git"
        destination.mkdir(parents=True)
        (destination / "config").write_text('[user]\n name = Original\n')
        # Exercise migration of the old managed ~/.gitconfig link too.
        (self.home / ".gitconfig").symlink_to(self.checkout / "home/.gitconfig")
        self.run_bash('bash home/setup/git.sh enable')
        self.assertFalse((self.home / ".gitconfig").is_symlink())
        output = self.run_bash('git config --global --includes --get user.name')
        self.assertEqual(output.strip(), "Private Machine")
        self.run_bash('DOTFILES_RESTORE_BACKUPS=1 bash home/setup/git.sh disable')
        self.assertFalse(destination.is_symlink())
        self.assertEqual((destination / "config").read_text(), '[user]\n name = Original\n')

    def test_scripts_restore_uses_the_same_names_as_install(self):
        (self.checkout / "scripts/clipboard-code").mkdir(parents=True)
        shutil.copy2(REPOSITORY / "scripts/setup.sh", self.checkout / "scripts/setup.sh")
        files = {
            "backup_gpg": "backup_gpg.sh", "restore_gpg": "restore_gpg.sh",
            "save_installed_packages": "save_installed_packages.sh",
            "update_arch": "update_arch.sh", "tmux_sessionizer": "tmux_sessionizer.sh",
            "clipboard-code": "clipboard-code/clipboard-code.sh",
            "ccode": "clipboard-code/clipboard-code.sh",
        }
        destination = self.home / ".local/scripts"
        destination.mkdir(parents=True)
        for name, source in files.items():
            (self.checkout / "scripts" / source).touch()
            (destination / name).write_text("original " + name)
        self.run_bash('bash scripts/setup.sh enable')
        self.assertTrue(all((destination / name).is_symlink() for name in files))
        self.run_bash('DOTFILES_RESTORE_BACKUPS=1 bash scripts/setup.sh disable')
        for name in files:
            self.assertFalse((destination / name).is_symlink())
            self.assertEqual((destination / name).read_text(), "original " + name)

    @unittest.skipUnless(shutil.which("nvim"), "requires Neovim")
    def test_nvim_local_hooks_bracket_shared_setup_without_installing_plugins(self):
        config = self.home / ".config/nvim"
        config.mkdir(parents=True)
        (config / "init.local.lua").write_text(
            'vim.g.local_top_level = true\n'
            'return {\n'
            ' before_init = function() vim.g.local_before = true end,\n'
            ' after_init = function()\n'
            '  assert(vim.g.shared_loaded == true)\n'
            '  vim.opt.tabstop = 8\n'
            ' end,\n'
            '}\n'
        )
        runner = self.checkout / "check-hooks.lua"
        runner.write_text(
            'for _, name in ipairs({ "options", "autocmds", "plugins.editor",\n'
            ' "plugins.tools", "plugins.coding", "plugins.testing", "plugins.ui", "lsp" }) do\n'
            ' package.loaded[name] = {}\n'
            'end\n'
            'package.loaded["config.pack"] = { setup = function()\n'
            ' assert(vim.g.local_top_level == true and vim.g.local_before == true)\n'
            'end }\n'
            'package.loaded["config.mappings"] = { setup = function()\n'
            ' vim.g.shared_loaded = true; vim.opt.tabstop = 4\n'
            'end }\n'
            f'dofile({str(REPOSITORY / "nvim/init.lua")!r})\n'
            'assert(vim.o.tabstop == 8)\n'
        )
        self.run_bash('nvim --clean --headless -l "$1"', runner)


if __name__ == "__main__":
    unittest.main()
