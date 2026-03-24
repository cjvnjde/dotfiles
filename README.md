# My Personal Dotfiles

A personal collection of dotfiles for macOS and Linux, designed for a consistent and productive development environment. This setup is modular, managed by a simple setup script, and consistently themed with **Catppuccin Mocha**.

-----

## Software Overview

| Category           | Tools                                              |
| ------------------ | -------------------------------------------------- |
| **Window Manager** | `Sway`, `Hyprland`, `Niri`                         |
| **Status Bar**     | `Waybar`                                           |
| **Terminal**       | `Alacritty`, `Kitty`, `Ghostty`                    |
| **Shell**          | `Zsh` (with Oh My Zsh, Atuin, Zoxide)              |
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
  - `zsh` & [oh-my-zsh](https://ohmyz.sh/): The primary shell environment.
  - [zsh-syntax-highlighting](https://github.com/zsh-users/zsh-syntax-highlighting/blob/master/INSTALL.md)
  - [zsh-autosuggestions](https://github.com/zsh-users/zsh-autosuggestions/blob/master/INSTALL.md)
  - [zsh-defer](https://github.com/romkatv/zsh-defer): Deferred execution for faster shell startup.
  - [Nerd Fonts](https://www.nerdfonts.com/): Required for icons (this config uses **FiraCode Nerd Font**).

- **Terminal Tools**:

  - [atuin](https://github.com/atuinsh/atuin): Enhanced shell history (installed via its own installer).
  - [bat](https://github.com/sharkdp/bat): A `cat` clone with syntax highlighting.
  - [eza](https://github.com/eza-community/eza): A modern replacement for `ls`.
  - [fzf](https://github.com/junegunn/fzf): A command-line fuzzy finder.
  - [delta](https://github.com/dandavison/delta): A viewer for git diffs.
  - [neovim](https://neovim.io/): The primary text editor.
  - [ripgrep](https://github.com/BurntSushi/ripgrep): A fast line-oriented search tool.
  - [zoxide](https://github.com/ajeetdsouza/zoxide): A smarter `cd` command.
  - [jq](https://jqlang.org/): A command-line JSON parser.
  - [mise](https://mise.jdx.dev/): Dev tools/runtimes manager (installed via its own installer).
  - [tldr](https://github.com/tldr-pages/tldr): Simplified man pages.
  - [tree-sitter-cli](https://github.com/tree-sitter/tree-sitter/blob/master/crates/cli/README.md): Required for Neovim.

- **GUI (Linux/Wayland)** — install only what you need for your chosen WM:

  - **Sway**: `sway`, `swaylock`, `swaybg`, `swayidle`, `xdg-desktop-portal-wlr`
  - **Hyprland**: `hyprland`, `hyprpaper`, `hypridle`, `hyprlock`
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
sudo pacman -S zsh git
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
git clone https://github.com/romkatv/zsh-defer ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-defer

# Terminal tools
sudo pacman -S bat eza fzf git-delta ghostty jq neovim ripgrep tldr zoxide
cargo install --locked tree-sitter-cli

# Installed via their own installers (not pacman)
curl https://mise.run | sh
curl --proto '=https' --tlsv1.2 -LsSf https://setup.atuin.sh | sh

# Wayland common
sudo pacman -S waybar rofi rofi-calc dunst libnotify grim slurp satty wl-clipboard wf-recorder

# Sway
sudo pacman -S sway swaylock swaybg swayidle xdg-desktop-portal-wlr

# Hyprland (install instead of / in addition to Sway)
sudo pacman -S hyprland hyprpaper hypridle hyprlock

# Niri (install instead of / in addition to Sway)
sudo pacman -S niri xwayland-satellite swaybg

# Audio & Bluetooth
sudo pacman -S pipewire wireplumber bluez bluez-utils bluetui
```

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

3. **Set the Waybar target** (only needed if you use Waybar):

    ```bash
    echo "sway" > waybar/target        # or hyprland, niri
    ```

4. **Run the setup script:**

    ```bash
    bash setup.sh
    ```

-----

## How It Works

### Module System

The setup is fully module-based. The root `setup.sh` does three things:

1. Reads `.modules` (and `.modules.local`) to determine which modules are enabled.
2. Discovers all module setup scripts automatically.
3. Calls each module's `setup.sh` with `enable` or `disable`.

Each module owns its own setup logic — the root script has no hardcoded paths or destinations.

### Module Types

**Directory modules** — most modules are entire config directories (e.g. `nvim`, `sway`, `alacritty`). They contain a `setup.sh` that symlinks the directory to the right place:

```
alacritty/setup.sh   → symlinks alacritty/ to ~/.config/alacritty
sway/setup.sh        → symlinks sway/     to ~/.config/sway
nvim/setup.sh        → symlinks nvim/     to ~/.config/nvim
```

**Single-file modules** — configs that are just one file live in `home/` and have their setup scripts in `home/setup/`:

```
home/setup/zshrc.sh    → symlinks home/.zshrc      to ~/.zshrc
home/setup/git.sh      → symlinks home/.gitconfig   to ~/.gitconfig
home/setup/wezterm.sh  → symlinks home/.wezterm.lua to ~/.wezterm.lua
```

**Custom modules** — some modules need more than a single symlink and have custom logic:

- `scripts/setup.sh` — creates `~/.local/scripts/` as a real directory and symlinks individual scripts into it (including `ccode` and `clipboard-code` aliases).
- `waybar/setup.sh` — symlinks shared files (`style.css`, `scripts/`) plus the active config based on `waybar/target`.

### Available Modules

| Module       | Destination                        | Notes                          |
| ------------ | ---------------------------------- | ------------------------------ |
| `nvim`       | `~/.config/nvim`                   |                                |
| `alacritty`  | `~/.config/alacritty`              |                                |
| `kitty`      | `~/.config/kitty`                  |                                |
| `ghostty`    | `~/.config/ghostty`                |                                |
| `zshrc`      | `~/.zshrc`                         | Sources `~/.zshrc_local` if it exists |
| `git`        | `~/.gitconfig`                     |                                |
| `ideavim`    | `~/.ideavimrc`                     |                                |
| `wezterm`    | `~/.wezterm.lua`                   |                                |
| `opencode`   | `~/.config/opencode/opencode.json` |                                |
| `scripts`    | `~/.local/scripts/*`               | Individual script symlinks     |
| `atuin`      | `~/.config/atuin`                  |                                |
| `bat`        | `~/.config/bat`                    |                                |
| `zellij`     | `~/.config/zellij`                 |                                |
| `tmux`       | `~/.config/tmux`                   |                                |
| `sway`       | `~/.config/sway`                   | See [sway/README.md](sway/README.md) |
| `hyprland`   | `~/.config/hypr`                   |                                |
| `niri`       | `~/.config/niri`                   |                                |
| `rofi`       | `~/.config/rofi`                   |                                |
| `waybar`     | `~/.config/waybar`                 | Uses `waybar/target` to pick config |
| `dunst`      | `~/.config/dunst`                  |                                |

### Waybar

Waybar has per-environment configs (`sway/`, `hyprland/`, `niri/`) that are all symlinked into `~/.config/waybar/`. The active one is selected via a `config.jsonc` symlink based on the `waybar/target` file.

**Switch the active config:**

```bash
echo "hyprland" > waybar/target   # switch to hyprland config
bash setup.sh                     # re-run to apply
```

Supported targets: `sway`, `hyprland`, `niri`.

For machine-specific overrides, create `waybar/target.local` instead — it takes priority and is git-ignored.

### Local Overrides

Several config files support machine-specific overrides that are git-ignored:

| File                  | Purpose                                           |
| --------------------- | ------------------------------------------------- |
| `.modules.local`      | Override enabled modules (supports `!module` to disable) |
| `waybar/target.local` | Override the active Waybar environment             |
| `~/.zshrc_local`      | Private aliases, env vars, machine-specific shell config |

**Example `.modules.local`** — enable everything from `.modules` but drop sway and add hyprland:

```
!sway
hyprland
```

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
    cd ~/dotfiles && git pull --recurse-submodules
    bash setup.sh
    ```

- **Conflicts:** If a destination already exists (and isn't the expected symlink), the setup backs it up to `<path>.bak` before linking.

- **Submodules:** Most modules are git submodules. Changes to module setup scripts need to be committed inside the submodule first, then the parent repo pointer updated.
