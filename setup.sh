#!/bin/bash

# Define the dotfiles directory
DOTFILES_DIR="$HOME/dotfiles"

# Define the configurations and their target locations
dotfiles=(
  "nvim:$HOME/.config/nvim"
  "tmux:$HOME/.config/tmux"
  "alacritty:$HOME/.config/alacritty"
  "home/.zshrc:$HOME/.zshrc"
  "home/.ideavimrc:$HOME/.ideavimrc"
  "scripts:$HOME/.local/scripts"
  "sway:$HOME/.config/sway"
  "waybar:$HOME/.config/waybar"
  "lf:$HOME/.config/lf"
  "rofi:$HOME/.config/rofi"
)

# Function to create a backup
backup() {
  local target="$1"
  local backup="$target.bak"
  local count=1

  # Check if a backup already exists, and create a new name to avoid overwriting
  while [ -e "$backup" ]; do
    backup="$target.bak$count"
    ((count++))
  done

  # Make the backup
  cp -a "$target" "$backup"
  echo "Backup created at $backup"
}

# Function to remove the original and create a symlink
overwrite_and_link() {
  local src="$1"
  local dest="$2"

  # Ask user for confirmation
  read -p "File $dest already exists. Do you want to overwrite it? (y/N): " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Create a backup
    backup "$dest"
    # Remove the original file/directory
    rm -rf "$dest"
    # Create the symlink
    ln -s "$src" "$dest"
    echo "Symlink created for $dest"
  else
    echo "Skipped $dest"
  fi
}

# Function to create a symbolic link
create_symlink() {
  local src="$1"
  local dest="$2"
  
  # Check if the source config exists
  if [ ! -e "$src" ]; then
    echo "Warning: Config $src does not exist"
    return
  fi

  # Create parent directory for the destination if it doesn't exist
  local dest_dir=$(dirname "$dest")
  mkdir -p "$dest_dir"

  # Check if the destination already exists
  if [ -e "$dest" ]; then
    # Check if it is already a symlink pointing to the correct location
    if [ "$(readlink -f "$dest")" = "$src" ]; then
      echo "Symlink already exists for $dest"
    else
      overwrite_and_link "$src" "$dest"
    fi
  else
    # Create the symlink
    ln -s "$src" "$dest"
    echo "Symlink created for $dest"
  fi
}

# Main script execution
echo "Setting up symlinks..."
for item in "${dotfiles[@]}"; do
  IFS=":" read -r src dest <<< "$item"
  src="$DOTFILES_DIR/$src"
  create_symlink "$src" "$dest"
done

echo "Symlinks setup complete."

