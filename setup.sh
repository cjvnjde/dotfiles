#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

# ====== CONFIG ======
DOTFILES_DIR="${DOTFILES_DIR:-"$HOME/dotfiles"}"

# name|repo_relative|destination_absolute (use $HOME literal in the right column)
read -r -d '' MODULE_MAP_RAW <<'EOF' || true
nvim|nvim|$HOME/.config/nvim
alacritty|alacritty|$HOME/.config/alacritty
zshrc|home/.zshrc|$HOME/.zshrc
ideavim|home/.ideavimrc|$HOME/.ideavimrc
wezterm|home/.wezterm.lua|$HOME/.wezterm.lua
git|home/.gitconfig|$HOME/.gitconfig
scripts|scripts|$HOME/.local/scripts
scripts|scripts/clipboard-code/clipboard-code.sh|$HOME/.local/scripts/ccode
atuin|atuin|$HOME/.config/atuin
bat|bat|$HOME/.config/bat
zellij|zellij|$HOME/.config/zellij
kitty|kitty|$HOME/.config/kitty
sway|sway|$HOME/.config/sway
rofi|rofi|$HOME/.config/rofi
waybar|waybar|$HOME/.config/waybar
dunst|dunst|$HOME/.config/dunst
onedrive|onedrive|$HOME/.config/onedrive
hyprland|hyprland|$HOME/.config/hypr
ghostty|ghostty|$HOME/.config/ghostty
niri|niri|$HOME/.config/niri
EOF

DEFAULT_FILE="$DOTFILES_DIR/.modules"
LOCAL_FILE="$DOTFILES_DIR/.modules.local"

# ====== LOGGING ======
log()      { printf '%s\n' "$*"; }
info()     { printf '[INFO] %s\n' "$*"; }
warn()     { printf '[WARN] %s\n' "$*" >&2; }
error()    { printf '[ERR ] %s\n' "$*" >&2; }
success()  { printf '[ OK ] %s\n' "$*"; }

trap 'error "Failed at line $LINENO: $BASH_COMMAND"' ERR

# ====== HELPERS ======
trim_comment() {
  local line="${1%%#*}"
  line="${line#"${line%%[![:space:]]*}"}"
  line="${line%"${line##*[![:space:]]}"}"
  printf '%s' "$line"
}

resolve_path() {
  local path="$1"
  
  if [ -L "$path" ] && [ ! -e "$path" ]; then
    readlink "$path" 2>/dev/null || printf '%s\n' "$path"
    return
  fi
  
  if command -v realpath >/dev/null 2>&1; then
    realpath "$path" 2>/dev/null || printf '%s\n' "$path"
  elif command -v readlink >/dev/null 2>&1; then
    readlink -f "$path" 2>/dev/null || printf '%s\n' "$path"
  else
    printf '%s\n' "$path"
  fi
}

backup_then_rm() {
  local target="$1"
  
  [ -e "$target" ] || [ -L "$target" ] || return 0
  
  local backup="$target.bak"
  local counter=1
  while [ -e "$backup" ]; do
    backup="$target.bak$counter"
    counter=$((counter + 1))
  done
  
  if cp -a "$target" "$backup" 2>/dev/null; then
    rm -rf "$target"
    info "Backup → $backup"
  else
    warn "Could not create backup, removing: $target"
    rm -rf "$target"
  fi
}

link_exact() {
  local src="$1"
  local dest="$2"
  
  if [ ! -e "$src" ]; then
    warn "Source missing: $src"
    return 1
  fi
  
  mkdir -p "$(dirname "$dest")"
  
  if [ -L "$dest" ]; then
    local current_resolved src_resolved
    current_resolved="$(resolve_path "$dest")"
    src_resolved="$(resolve_path "$src")"
    
    if [ "$current_resolved" = "$src_resolved" ]; then
      return 0
    fi
  fi
  
  if [ -e "$dest" ] || [ -L "$dest" ]; then
    backup_then_rm "$dest"
  fi
  
  ln -s "$src" "$dest"
  return 0
}

# ====== ENABLED SET ======
enabled_list=""

in_enabled() {
  printf '%s' "$enabled_list" | grep -qx -- "$1" || return 1
}

enable_mod() {
  local name="$1"
  in_enabled "$name" || enabled_list="${enabled_list}${name}"$'\n'
}

disable_mod() {
  local name="$1"
  enabled_list="$(printf '%s' "$enabled_list" | grep -vx -- "$name" || true)"
}

process_file() {
  local file="$1"
  [ -f "$file" ] || return 0
  
  info "Reading modules from: $file"
  
  while IFS= read -r raw || [ -n "$raw" ]; do
    local line
    line="$(trim_comment "$raw")"
    [ -z "$line" ] && continue
    
    case "$line" in
      '!'*) disable_mod "${line#\!}";;
      *)    enable_mod "$line";;
    esac
  done < "$file"
}

# ====== START ======
info "DOTFILES_DIR = $DOTFILES_DIR"

if [ ! -d "$DOTFILES_DIR" ]; then
  error "DOTFILES_DIR not found"
  exit 1
fi

process_file "$DEFAULT_FILE"
process_file "$LOCAL_FILE"

info "Enabled modules:"
if [ -n "$enabled_list" ]; then
  printf '%s' "$enabled_list" | sed '/^$/d' | sort | sed 's/^/  - /'
else
  echo "  (none)"
fi
echo

# ====== PARSE MODULE MAP ======
MODULE_MAP=""
while IFS= read -r line || [ -n "$line" ]; do
  [ -z "$line" ] && continue
  IFS='|' read -r name rel dst_tpl <<<"$line"
  dst="${dst_tpl//\$HOME/$HOME}"
  MODULE_MAP+="${name}|${rel}|${dst}"$'\n'
done <<<"$MODULE_MAP_RAW"

# ====== APPLY ======
created=()
updated=()
already_ok=()
unlinked=()
skipped=()

info "Linking enabled modules…"
while IFS= read -r row || [ -n "$row" ]; do
  [ -z "$row" ] && continue
  IFS='|' read -r name rel dst <<<"$row"
  
  if in_enabled "$name"; then
    src="$DOTFILES_DIR/$rel"
    
    if [ ! -e "$src" ]; then
      warn "Missing source for '$name': $src"
      skipped+=("$dst")
      continue
    fi
    
    # Check if already correct
    if [ -L "$dst" ]; then
      current_resolved="$(resolve_path "$dst")"
      src_resolved="$(resolve_path "$src")"
      
      if [ "$current_resolved" = "$src_resolved" ]; then
        already_ok+=("$dst")
        info "Up-to-date → $dst"
        continue
      fi
    fi
    
    # Determine if creating or updating
    if [ -e "$dst" ] || [ -L "$dst" ]; then
      updated+=("$dst")
    else
      created+=("$dst")
    fi
    
    if link_exact "$src" "$dst"; then
      success "Symlink → $dst"
    fi
  fi
done <<<"$MODULE_MAP"

echo
info "Unlinking disabled modules…"
while IFS= read -r row || [ -n "$row" ]; do
  [ -z "$row" ] && continue
  IFS='|' read -r name rel dst <<<"$row"
  
  if ! in_enabled "$name"; then
    if [ -L "$dst" ]; then
      current_resolved="$(resolve_path "$dst")"
      expected_resolved="$(resolve_path "$DOTFILES_DIR/$rel")"
      
      if [ "$current_resolved" = "$expected_resolved" ]; then
        rm -f "$dst"
        unlinked+=("$dst")
        success "Unlinked → $dst"
      else
        info "Skip (not managed) → $dst"
      fi
    fi
  fi
done <<<"$MODULE_MAP"

# ====== EXTRAS ======
touch "$HOME/.hushlogin" 2>/dev/null && info "Ensured ~/.hushlogin"

if [ -x "$DOTFILES_DIR/after_setup.sh" ]; then
  info "Running after_setup.sh…"
  "$DOTFILES_DIR/after_setup.sh"
fi

# ====== SUMMARY ======
echo
log "========== SUMMARY =========="

[ "${#created[@]}" -gt 0 ] && {
  log "Created (${#created[@]}):"
  printf '  + %s\n' "${created[@]}"
}

[ "${#updated[@]}" -gt 0 ] && {
  log "Updated (${#updated[@]}):"
  printf '  ~ %s\n' "${updated[@]}"
}

[ "${#unlinked[@]}" -gt 0 ] && {
  log "Unlinked (${#unlinked[@]}):"
  printf '  - %s\n' "${unlinked[@]}"
}

[ "${#skipped[@]}" -gt 0 ] && {
  log "Skipped (missing source) (${#skipped[@]}):"
  printf '  ! %s\n' "${skipped[@]}"
}

[ "${#already_ok[@]}" -gt 0 ] && {
  log "Already OK (${#already_ok[@]}):"
  if [ "${#already_ok[@]}" -le 5 ]; then
    printf '  = %s\n' "${already_ok[@]}"
  else
    printf '  = %s\n' "${already_ok[@]}" | head -5
    log "  ... and $((${#already_ok[@]} - 5)) more"
  fi
}

log "============================="
success "Done."
