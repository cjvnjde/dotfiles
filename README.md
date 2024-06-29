# Dotfiles Repository

This repository manages configuration files for various tools and utilities using Git submodules, helping to maintain a consistent and easily reproducible development environment across different machines.

## Getting Started

### Requirements

#### Global deps 

- [Nerd Fonts](https://www.nerdfonts.com/)
- [Oh My Zsh](https://ohmyz.sh/)
- [asdf](https://asdf-vm.com) package version manager

#### Terminal deps
- [atuin](https://github.com/atuinsh/atuin) search in terminal history
- [eza](https://github.com/eza-community/eza) lf alternative
- [fzf](https://github.com/junegunn/fzf)

#### Home deps
- [zoxide](https://github.com/ajeetdsouza/zoxide) better autojump
- [zsh node-bin](https://github.com/remcohaszing/zsh-node-bin)

#### nvim deps
- [fzf](https://github.com/junegunn/fzf)
- [ripgrep](https://github.com/BurntSushi/ripgrep)

## Notes

Core theme - catppuccin Mocha

### Installation

1. Clone the repository along with its submodules:

    ```shell
    git clone --recurse-submodules git@github.com:cjvnjde/dotfiles.git $HOME/dotfiles
    ```

2. Run the setup script to create symbolic links for your dotfiles:

    ```shell
    $HOME/dotfiles/setup.sh
    ```

## Usage

### Adding New Dotfiles

1. Add the external configuration repository as a submodule:

    ```sh
    git submodule add git@github.com:cjvnjde/reponame.git path/to/repo
    ```

2. Update the associative array in the `setup.sh` script:

    ```bash
    dotfiles=(
    ...
    "path/to/file:path/to/symbolic"
    )
    ```

3. Run the setup script to create the symbolic link:

    ```sh
    $HOME/dotfiles/setup.sh
    ```

4. Commit and push your changes:

    ```sh
    git add .
    git commit -m "Add repo submodule"
    git push
    ```

### Updating Dotfiles

1. Pull the latest changes, including submodule updates:

    ```sh
    git pull --recurse-submodules
    ```

2. Run the setup script to apply the changes:

    ```sh
    ./setup.sh
    ```

## Platform Specific Configuration for Zsh

1. **Navigate to Your Home Directory**: 

    ```sh
    cd $HOME
    ```

2. **Create the `.zshrc_local` File**: 

    If it doesn't already exist, create the `.zshrc_local` file.

    ```sh
    touch .zshrc_local
    ```

3. **Edit the `.zshrc_local` File**: 

    Open the file in your preferred text editor.

    ```sh
    nano .zshrc_local  # or use vim, code, etc.
    ```

    Add your platform-specific configurations, aliases, environment variables, etc., to this file.
