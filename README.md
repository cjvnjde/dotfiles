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

-----

## Installation

1. **Clone the repository** and its submodules:

    ```bash
    git clone --recurse-submodules git@github.com:cjvnjde/dotfiles.git $HOME/dotfiles
    ```

2. **Run the setup script** to create the necessary symbolic links:

    ```bash
    cd $HOME/dotfiles/setup.sh
    ```

### Customization

You can control which configurations are installed by editing `$HOME/.dotfiles/.modules`. For machine-specific overrides, create a file at `$HOME/.dotfiles/.modules.local` (this file is ignored by Git).

For example, to disable `sway`, add `!sway` to your `.modules.local` file.

```
!sway
```

#### Alacritty

The main `alacritty.toml` imports an `overrides.toml` file, which is ignored by Git. You can create `$HOME/dotfiles/alacritty/overrides.toml` to set options that apply only to the current machine

```toml
# $HOME/dotfiles/alacritty/overrides.toml

[window]
decorations = "Full"
```

#### Zsh

The `.zshrc` file will automatically source `$HOME/.zshrc_local` if it exists. This is the ideal place for private aliases, environment variables, or sourcing scripts that are only present on one machine.

```bash
# ~/.zshrc_local

alias work-project="cd ~/projects/work/my-secret-project"
export GITHUB_TOKEN="your_token_here"
```

-----

## Management

- **Updating**: Pull the latest changes for the repository and all submodules.

    ```bash
    cd ~/dotfiles && git pull --recurse-submodules
    ```
