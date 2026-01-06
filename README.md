# My Personal Dotfiles

A personal collection of dotfiles for macOS and Linux, designed for a consistent and productive development environment. This setup is modular, managed by a simple setup script, and consistently themed with **Catppuccin Mocha**.

-----

## Software Overview

| Category          | Tools                                            |
| ----------------- | ------------------------------------------------ |
| **Window Manager**| `Sway`, `Hyprland`, `Niri`                         |
| **Terminal** | `Alacritty`, `Kitty`, `Zellij`                   |
| **Shell** | `Zsh` (with Oh My Zsh, Atuin, Zoxide)            |
| **Editor** | `Neovim`                                         |
| **Git UI** | `delta`, `lazygit`                           |
| **File Manager** | `lf`                                             |
| **Utilities** | `bat`, `eza`, `fzf`, `ripgrep`, `tldr`, `thefuck`  |

-----

## Requirements

To use this configuration, you'll need to install the following software.

- **Core**:

  - `git`: For cloning and managing the repository.
  - `zsh` & [oh-my-zsh](https://ohmyz.sh/): The primary shell environment.
  - [zsh-syntax-highlighting](https://github.com/zsh-users/zsh-syntax-highlighting/blob/master/INSTALL.md)
  - [zsh-autosuggestions](https://github.com/zsh-users/zsh-autosuggestions/blob/master/INSTALL.md)
  - [Nerd Fonts](https://www.nerdfonts.com/): Required for icons (this config uses **FiraCode Nerd Font**).

- **Terminal Tools**:

  - [atuin](https://github.com/atuinsh/atuin): For enhanced shell history.
  - [bat](https://github.com/sharkdp/bat): A `cat` clone with syntax highlighting.
  - [eza](https://github.com/eza-community/eza): A modern replacement for `ls`.
  - [fzf](https://github.com/junegunn/fzf): A command-line fuzzy finder.
  - [delta](https://github.com/dandavison/delta): A viewer for git diffs.
  - [neovim](https://neovim.io/): The primary text editor.
  - [ripgrep](https://github.com/BurntSushi/ripgrep): A fast line-oriented search tool.
  - [zoxide](https://github.com/ajeetdsouza/zoxide): A smarter `cd` command.
  - [jq](https://jqlang.org/): A command-line JSON parser.
  - [mise](https://mise.jdx.dev/): Dev tools/runtimes manager.
  - [zellij](https://zellij.dev/): A terminal workspace.

- **GUI (Linux/Wayland)**:

  - `Sway` or `Hyprland`: Tiling window managers.
  - `Waybar`: A status bar for Wayland.
  - `Rofi`: An application launcher.
  - `Dunst`: For notifications.
  - `grim` & `slurp`: For screenshots.

### Arch Linux

```bash
sudo pacman -Syu zsh git
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
sudo pacman -Syu atuin bat eza fzf git-delta neovim ripgrep zoxide jq
curl https://mise.run | sh
```

```bash
sudo pacman -Syu dunst libnotify sway swaylock swaybg swayidle waybar rofi rofi-calc wl-clipboard wf-recorder grim slurp
```

-----

## Installation

1. **Clone the repository** and its submodules:

    ```bash
    git clone --recurse-submodules git@github.com:cjvnjde/dotfiles.git $HOME/dotfiles
    ```

2. You can control which configurations are installed by creating `$HOME/dotfiles/.modules`.

```bash
cp .modules.example .modules
```

1. **Run the setup script** to create the necessary symbolic links:

    ```bash
    sh $HOME/dotfiles/setup.sh
    ```

## Management

- **Updating**: Pull the latest changes for the repository and all submodules.

    ```bash
    cd ~/dotfiles && git pull --recurse-submodules
    ```
