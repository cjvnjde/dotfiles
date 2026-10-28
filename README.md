# My Personal Dotfiles

A personal collection of dotfiles for macOS and Linux, designed for a consistent and productive development environment. This setup is modular, managed by a simple setup script, and consistently themed with **Catppuccin Mocha**.

## Repositories

- [dotfiles](https://github.com/cjvnjde/dotfiles)
- [dotfiles.nvim](https://github.com/cjvnjde/dotfiles.nvim)
- [dotfiles.agents](https://github.com/cjvnjde/dotfiles.agents)
- [dotfiles.home](https://github.com/cjvnjde/dotfiles.home)
- [dotfiles.sway](https://github.com/cjvnjde/dotfiles.sway)
- [dotfiles.scripts](https://github.com/cjvnjde/dotfiles.scripts)
- [dotfiles.ghostty](https://github.com/cjvnjde/dotfiles.ghostty)
- [dotfiles.tmux](https://github.com/cjvnjde/dotfiles.tmux)
- [dotfiles.waybar](https://github.com/cjvnjde/dotfiles.waybar)
- [dotfiles.zellij](https://github.com/cjvnjde/dotfiles.zellij)
- [dotfiles.atuin](https://github.com/cjvnjde/dotfiles.atuin)
- [dotfiles.rofi](https://github.com/cjvnjde/dotfiles.rofi)
- [dotfiles.bat](https://github.com/cjvnjde/dotfiles.bat)
- [dotfiles.alacritty](https://github.com/cjvnjde/dotfiles.alacritty)
- [dotfiles.dunst](https://github.com/cjvnjde/dotfiles.dunst)
- [dotfiles.hyprland](https://github.com/cjvnjde/dotfiles.hyprland)
- [dotfiles.kitty](https://github.com/cjvnjde/dotfiles.kitty)
- [dotfiles.niri](https://github.com/cjvnjde/dotfiles.niri)
- [dotfiles.nvim2](https://github.com/cjvnjde/dotfiles.nvim2)
- [dotfiles.lf](https://github.com/cjvnjde/dotfiles.lf)
- [dotfiles.onedrive](https://github.com/cjvnjde/dotfiles.onedrive)

-----

## Software Overview

| Category           | Tools                                              |
| ------------------ | -------------------------------------------------- |
| **Window Manager** | `Sway`, `Hyprland`, `Niri`                         |
| **Status Bar**     | `Waybar`                                           |
| **Terminal**       | `Alacritty`, `Kitty`, `Ghostty`                    |
| **Shell**          | `Zsh` (with Starship, Atuin, Zoxide)              |
| **Editor**         | `Neovim`                                           |
| **Multiplexer**    | `Zellij`, `Tmux`                                   |
| **Git**            | `delta`, `git-cliff`, `github-cli`                 |
| **Launcher**       | `Rofi` (+ `rofi-calc`)                             |
| **Notifications**  | `Dunst`                                            |
| **Screenshots**    | `grim`, `slurp`, `satty`                           |
| **File Manager**   | `lf`                                               |
| **Utilities**      | `bat`, `eza`, `fzf`, `ripgrep`, `jq`, `tldr`, `mise` |
| **TUI**            | `bluetui` (Bluetooth)                              |
| **Audio**          | `PipeWire`, `WirePlumber`                          |

-----

## Requirements

- **Core**:

  - `git`: For cloning and managing the repository.
  - `zsh` & [Starship](https://starship.rs/): The shell and prompt.
  - [zsh-syntax-highlighting](https://github.com/zsh-users/zsh-syntax-highlighting/blob/master/INSTALL.md)
  - [zsh-autosuggestions](https://github.com/zsh-users/zsh-autosuggestions/blob/master/INSTALL.md)
  - [Nerd Fonts](https://www.nerdfonts.com/): Required for icons (this config uses **FiraCode Nerd Font**).

- **Terminal Tools**:

  - [atuin](https://github.com/atuinsh/atuin): Enhanced shell history.
  - [bat](https://github.com/sharkdp/bat): A `cat` clone with syntax highlighting.
  - [eza](https://github.com/eza-community/eza): A modern replacement for `ls`.
  - [fzf](https://github.com/junegunn/fzf): A command-line fuzzy finder.
  - [delta](https://github.com/dandavison/delta): A viewer for git diffs.
  - [neovim](https://neovim.io/): The primary text editor.
  - [ripgrep](https://github.com/BurntSushi/ripgrep): A fast line-oriented search tool.
  - [zoxide](https://github.com/ajeetdsouza/zoxide): A smarter `cd` command.
  - [jq](https://jqlang.org/): A command-line JSON parser.
  - [mise](https://mise.jdx.dev/): Dev tools/runtimes manager.
  - [tldr](https://github.com/tldr-pages/tldr): Simplified man pages.
  - [tree-sitter-cli](https://github.com/tree-sitter/tree-sitter/blob/master/crates/cli/README.md): Required for Neovim.

- **GUI (Linux/Wayland)** — install only what you need for your chosen WM:

  - **Sway**: `sway`, `swaylock`, `swaybg`, `swayidle`, `xdg-desktop-portal-wlr`
  - **Hyprland**: `hyprland`, `quickshell`, `hypridle`, `hyprlock`
  - **Niri**: `niri`, `xwayland-satellite`, `swaybg`
  - **Common**: `waybar`, `rofi`, `rofi-calc`, `dunst`, `libnotify`
  - **Screenshots**: `grim`, `slurp`, `satty` (annotation editor), `wf-recorder` (screen recording)
  - **Clipboard**: `wl-clipboard`
  - **Audio**: `pipewire`, `wireplumber`
  - **Bluetooth**: `bluez`, `bluez-utils`, `bluetui` (TUI manager)

### Arch Linux

A full package list is maintained in [`packages/`](packages/):
- `packages/official_packages.txt` — pacman packages
- `packages/aur_packages.txt` — AUR packages

Below are the packages relevant to these dotfiles.

```bash
# Shell & core
sudo pacman -S zsh git starship zsh-syntax-highlighting zsh-autosuggestions

# Terminal tools
sudo pacman -S atuin bat eza fzf git-delta ghostty jq neovim ripgrep tldr tree-sitter-cli zellij zoxide

# Wayland common
sudo pacman -S waybar rofi rofi-calc dunst libnotify grim slurp satty wl-clipboard wf-recorder

# Sway
sudo pacman -S sway swaylock swaybg swayidle xdg-desktop-portal-wlr

# Hyprland (install instead of / in addition to Sway)
sudo pacman -S hyprland quickshell hypridle hyprlock

# Niri (install instead of / in addition to Sway)
sudo pacman -S niri xwayland-satellite swaybg

# Audio & Bluetooth
sudo pacman -S pipewire wireplumber bluez bluez-utils bluetui
```

-----

## Omarchy

Install missing tools through Omarchy's package helper, after reviewing the
transaction. Use mise only for tools unavailable in the configured repositories;
do not use AUR, Cargo, npm, or standalone installers for this setup.

```bash
omarchy pkg add zsh zsh-autosuggestions zsh-syntax-highlighting atuin zellij ghostty git-delta ttf-firacode-nerd
```

Copy each module's local example to its gitignored local filename and customize
it before linking. Keep Omarchy theme includes, prompt selection, shell activation,
and other machine settings in those local files. Setup only links configuration;
it does not install these packages, change the login shell, or choose a default
terminal. Continue to use `omarchy update` for system updates.

-----

## Installation

1. **Clone the repository** and its submodules:

    ```bash
    git clone --recurse-submodules git@github.com:cjvnjde/dotfiles.git $HOME/dotfiles
    cd $HOME/dotfiles
    ```

2. **Choose which modules to enable** by creating a `.modules` file:

    ```bash
    cp .modules.example .modules
    ```

    Edit `.modules` to keep only the modules you need. Lines starting with `!` disable a previously enabled module (useful in `.modules.local`).

3. **Run the setup script:**

    ```bash
    bash setup.sh
    ```

-----

## How It Works

### Module System

The setup is fully module-based. The root `setup.sh` does three things:

1. Reads `.modules` (and `.modules.local`) to determine which modules are enabled.
2. Discovers all module setup scripts automatically.
3. Calls independent modules' `setup.sh` scripts concurrently with `enable` or `disable`.

Each module owns its own setup logic — the root script has no hardcoded paths or destinations.

### Parallel Execution

Run either script directly. Every independent module gets its own background job, with no worker limit or job-count configuration:

```bash
./setup.sh
./update.sh
```

Setup runs `tmux` and `ly` in a separate foreground phase after all background modules succeed, because they can prompt or request `sudo` access. Override the space-separated list when adding interactive modules or modules that share resources:

```bash
DOTFILES_SERIAL_MODULES="tmux ly my-module" bash setup.sh
```

An empty `DOTFILES_SERIAL_MODULES` allows every module to run in the background; use it only when none require terminal input or exclusive access. Background modules receive `/dev/null` as stdin so non-interactive installers, including `skills --yes`, cannot read or change the foreground terminal through stdin. Their output streams live and may interleave. Setup waits for all workers and only runs `after_setup.sh` if every module succeeds.

Update pulls the main repository with `--no-recurse-submodules`, then each submodule job switches to `main` and pulls with `--no-recurse-submodules`. Missing submodules are initialized inside their own jobs, not in a sequential fetch pass. Parent updates finish before their nested submodules are discovered and updated. The summary reports updated, skipped, and failed counts; any failure produces a nonzero exit status. Interrupting either script terminates active background workers.

### Module Types

**Directory modules** — most modules are entire config directories (e.g. `nvim`, `hyprland`, `alacritty`). They contain a `setup.sh` that symlinks the directory to the right place:

```
alacritty/setup.sh   → symlinks alacritty/ to ~/.config/alacritty
hyprland/setup.sh    → symlinks hyprland/ to ~/.config/hypr
nvim/setup.sh        → symlinks nvim/     to ~/.config/nvim
```

**Single-file modules** — configs that are just one file live in `home/` and have their setup scripts in `home/setup/`:

```
home/setup/zshrc.sh    → symlinks home/.zshrc      to ~/.zshrc
home/setup/git.sh      → symlinks home/git/        to ~/.config/git
home/setup/wezterm.sh  → symlinks home/.wezterm.lua to ~/.wezterm.lua
```

**Custom modules** — some modules need more than a single symlink and have custom logic:

- `scripts/setup.sh` — creates `~/.local/scripts/` as a real directory and symlinks individual scripts into it (including `ccode` and `clipboard-code` aliases).
- `agents/setup.sh` — uses `npx skills@latest` to install only the small global skill set for Pi, Codex, Claude Code, Zed, and universal agents; project skills remain opt-in.

### Available Modules

| Module       | Destination                        | Notes                          |
| ------------ | ---------------------------------- | ------------------------------ |
| `nvim`       | `~/.config/nvim`                   |                                |
| `alacritty`  | `~/.config/alacritty`              |                                |
| `kitty`      | `~/.config/kitty`                  |                                |
| `ghostty`    | `~/.config/ghostty`                |                                |
| `zshrc`      | `~/.zshrc`                         | Loads `home/.zshrc.local`       |
| `git`        | `$XDG_CONFIG_HOME/git` (default `~/.config/git`) | Includes `home/git/config.local` |
| `ideavim`    | `~/.ideavimrc`                     |                                |
| `wezterm`    | `~/.wezterm.lua`                   |                                |
| `opencode`   | `~/.config/opencode/opencode.json` |                                |
| `scripts`    | `~/.local/scripts/*`               | Individual script symlinks     |
| `agents`     | Global agent skill directories              | Managed with `npx skills@latest` for Pi, Codex, Claude Code, Zed, and universal agents |
| `atuin`      | `~/.config/atuin`                  |                                |
| `bat`        | `~/.config/bat`                    |                                |
| `zellij`     | `~/.config/zellij`                 |                                |
| `tmux`       | `~/.config/tmux`                   |                                |
| `hyprland`   | `~/.config/hypr`                   |                                |
| `ly`         | `/etc/ly/config.ini`                | Requires root access           |

### Local Overrides

Machine-specific overrides live inside their owning module and are gitignored
by that submodule. Copy a tracked example, remove `.example` from its name, and
keep the resulting local file private. Local files accept general configuration,
including options, paths, keybindings, plugins, and themes.

| File                  | Purpose                                           |
| --------------------- | ------------------------------------------------- |
| `.modules.local`      | Override enabled modules (supports `!module` to disable) |
| `nvim/init.local.lua` | Top-level Lua and optional `before_init` / `after_init` functions |
| `ghostty/config.local` | Any Ghostty settings; included after shared settings |
| `home/.zshrc.local`   | Early Zsh setup and optional `zshrc_local_after_init` function |
| `home/git/config.local` | Any Git sections; included last by `home/git/config` |

Neovim loads its local file before the shared configuration, calls `before_init`,
then calls `after_init` once shared options, plugins, LSP, and mappings are ready.
Top-level code and both hooks are optional. Zsh follows the same early/late order;
syntax highlighting loads after its late hook. Existing `~/.zshrc_local` files
remain a fallback until `home/.zshrc.local` is created; they load after shared
initialization to preserve their alias and keybinding overrides.

Ghostty loads `config.local` through its native optional include. On Omarchy,
`font-family = monospace` in that file follows the system font, and the optional
`~/.local/state/omarchy/current/theme/ghostty.conf` include supplies theme colors.
The shared font line is intentionally unquoted so the installed Omarchy font
setter does not rewrite the tracked preference.

Git links a directory at `${XDG_CONFIG_HOME:-$HOME/.config}/git` so its relative
`config.local` include works regardless of where the checkout lives. For a
separate work identity, add a conditional include in `home/git/config.local`
pointing to `work.local` beside it. All `home/git/*.local` files are gitignored.
Enable `git` in `.modules` and run the global `bash setup.sh` to link it;
setup does not migrate private files. Setup removes only the legacy `~/.gitconfig` symlink
owned by this checkout; an unrelated file is left alone and can override XDG Git
settings.
Edit private Git values with `git config --file /path/to/home/git/config.local`.
When inspecting includes with `git config --global`, add `--includes`.

**Example `.modules.local`** — enable everything from `.modules` but drop Alacritty and add Kitty:

```
!alacritty
kitty
```

-----

## Personal Agent Skills

Keep only deliberately global skills under `agents/skills/`. Add reusable project skills to the opt-in library:

```text
agents/library/<skill-name>/SKILL.md
```

Enable the `agents` module and run `bash setup.sh` to install the global configuration (`AGENTS.md`, `eco-mode`, and `skill-authoring`). Ask an agent to select only the needed packages from `agents/library/` and copy them into a project's host-supported skills directory. Library additions are never installed globally by setup. See [`agents/README.md`](agents/README.md) for selection, migration, installation, and removal behavior.

-----

## Adding a New Module

**Directory module** (e.g. `~/.config/foo`):

1. Add the config directory: `foo/`
2. Create `foo/setup.sh` following any existing module as a template (e.g. `alacritty/setup.sh`).
3. Add `foo` to `.modules`.

**Single-file module** (e.g. `~/.some_rc`):

1. Add the file to `home/` (e.g. `home/.some_rc`).
2. Create `home/setup/some_rc.sh` following `home/setup/git.sh` as a template.
3. Add `some_rc` to `.modules`.

The root `setup.sh` discovers modules automatically — no registration step needed.

-----

## Management

- **Re-run after changes:**

    ```bash
    bash ~/dotfiles/setup.sh
    ```

    The script is idempotent — running it again with no changes produces no output beyond info logs.

- **Update from remote:**

    ```bash
    cd ~/dotfiles && bash update.sh
    bash setup.sh
    ```

    `update.sh` switches each non-ignored submodule to `main` and pulls normally; it does not hard-reset local work. Missing `main` branches, checkout conflicts, and pull failures are reported as errors.

- **Conflicts:** Most modules back up an existing destination to `<path>.bak` before linking. The `agents` module delegates same-name skill handling to the `skills` CLI; unrelated skill names remain untouched.

- **Preview without changing files:**

    ```bash
    bash setup.sh --dry-run
    bash setup.sh --dry-run nvim ghostty git zshrc
    ```

    This shows module actions without executing module scripts or post-setup hooks.
    Supplying module names limits setup to those modules; each follows `.modules`.

- **Restore the previous configuration:**

    ```bash
    bash setup.sh --dry-run --restore nvim ghostty git
    bash setup.sh --restore nvim ghostty git
    ```

    Restore removes only links managed by this checkout and moves the newest
    numbered backup (`.bak`, `.bak1`, ... `.bak10`) back into place. Earlier backups
    remain available. Existing unmanaged paths are left untouched. Without names,
    restore visits only currently enabled modules. It skips post-setup hooks and
    does not reinstall anything. Ordinary disable still only unlinks; restoration
    must be requested explicitly. Backups are adjacent to their original paths,
    so for `~/.config/git` the backup is `~/.config/git.bak`.

- **Submodules:** Most modules are git submodules. Changes to module setup scripts need to be committed inside the submodule first, then the parent repo pointer updated.
