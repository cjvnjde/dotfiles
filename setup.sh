#!/bin/bash

DOTFILES_DIR="$HOME/dotfiles"

dotfiles=(
  "nvim:$HOME/.config/nvim"
#  "tmux:$HOME/.config/tmux"
  "alacritty:$HOME/.config/alacritty"
  "home/.zshrc:$HOME/.zshrc"
  "home/.ideavimrc:$HOME/.ideavimrc"
  "home/.gitconfig:$HOME/.gitconfig"
  "scripts:$HOME/.local/scripts"
  "sway:$HOME/.config/sway"
  "waybar:$HOME/.config/waybar"
#  "lf:$HOME/.config/lf"
  "rofi:$HOME/.config/rofi"
  "kitty:$HOME/.config/kitty"
  "dunst:$HOME/.config/dunst"
#  "onedrive:$HOME/.config/onedrive"
  "atuin:$HOME/.config/atuin"
  "bat:$HOME/.config/bat"
  "zellij:$HOME/.config/zellij"
  "hyprland:$HOME/.config/hypr"
  "ghostty:$HOME/.config/ghostty"
)

backup() {
  local target="$1"
  local backup="$target.bak"
  local count=1

  while [ -e "$backup" ]; do
    backup="$target.bak$count"
    ((count++))
  done

  cp -a "$target" "$backup"
  echo "Backup created at $backup"
}

overwrite_and_link() {
  local src="$1"
  local dest="$2"

  read -p "File $dest already exists. Do you want to overwrite it? (y/N): " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    backup "$dest"
    rm -rf "$dest"
    ln -s "$src" "$dest"
    echo "Symlink created for $dest"
  else
    echo "Skipped $dest"
  fi
}

create_symlink() {
  local src="$1"
  local dest="$2"
  
  if [ ! -e "$src" ]; then
    echo "Warning: Config $src does not exist"
    return
  fi

  local dest_dir=$(dirname "$dest")
  mkdir -p "$dest_dir"

  if [ -e "$dest" ]; then
    if [ "$(readlink -f "$dest")" = "$src" ]; then
      echo "Symlink already exists for $dest"
    else
      overwrite_and_link "$src" "$dest"
    fi
  else
    ln -s "$src" "$dest"
    echo "Symlink created for $dest"
  fi
}

echo "Setting up symlinks..."
for item in "${dotfiles[@]}"; do
  IFS=":" read -r src dest <<< "$item"
  src="$DOTFILES_DIR/$src"
  create_symlink "$src" "$dest"
done

echo "Symlinks setup complete."

sh "$DOTFILES_DIR/after_setup.sh"
