# Dotfiles Repository

This repository manages configuration files for various tools and utilities using Git submodules, helping to maintain a consistent and easily reproducible development environment across different machines.

## Getting Started

### Installation

1. Clone the repository along with its submodules:

    ```sh
    git clone --recurse-submodules git@github.com:cjvnjde/dotfiles.git $HOME/dotfiles
    cd $HOME/dotfiles
    ```

2. Run the setup script to create symbolic links for your dotfiles:

    ```sh
    ./setup.sh
    ```

## Usage

### Adding New Dotfiles

1. Add the external configuration repository as a submodule:

    ```sh
    git submodule add https://github.com/username/repo.git path/to/repo
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
    ./setup.sh
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
