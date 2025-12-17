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
waybar|waybar|$HOME/.config/waybar
dunst|dunst|$HOME/.config/dunst
onedrive|onedrive|$HOME/.config/onedrive
hyprland|hyprland|$HOME/.config/hypr
ghostty|ghostty|$HOME/.config/ghostty
niri|niri|$HOME/.config/niri
EOF

DEFAULT_FILE="$DOTFILES_DIR/.modules"        # optional (tracked)
LOCAL_FILE="$DOTFILES_DIR/.modules.local"    # per-machine (ignored)

# ====== LOGGING ======
log()      { printf '%s\n' "$*"; }
info()     { printf '[INFO] %s\n' "$*"; }
warn()     { printf '[WARN] %s\n' "$*" >&2; }
error()    { printf '[ERR ] %s\n' "$*" >&2; }
success()  { printf '[ OK ] %s\n' "$*"; }

trap 'error "Failed at line $LINENO: $BASH_COMMAND"' ERR

# ====== HELPERS ======
trim_comment() {
  # strip comments + trim
  local l="${1%%#*}"
  l="$(printf '%s' "$l" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
  printf '%s' "$l"
}

resolve_path() {
  if command -v realpath >/dev/null 2>&1; then realpath "$1"
  elif command -v readlink >/dev/null 2>&1; then readlink -f "$1" 2>/dev/null || printf '%s\n' "$1"
  else printf '%s\n' "$1"; fi
}

backup_then_rm() {
  local target
  target="$1"

  local b
  b="$target.bak"

  local n=1
  while [ -e "$b" ]; do
    b="$target.bak$n"
    n=$((n+1))
  done

  if [ -e "$target" ] || [ -L "$target" ]; then
    cp -a "$target" "$b" 2>/dev/null || true
    rm -rf "$target"
    [ -e "$b" ] && info "Backup → $b"
  fi
}

link_exact() {
  local src="$1" dest="$2"
  if [ ! -e "$src" ]; then warn "Missing source $src"; return; fi
  mkdir -p "$(dirname "$dest")"
  if [ -L "$dest" ]; then
    local cur; cur="$(resolve_path "$dest")"
    if [ "$cur" = "$(resolve_path "$src")" ]; then
      info "Up-to-date → $dest"
      return
    fi
  fi
  if [ -e "$dest" ] || [ -L "$dest" ]; then
    info "Replace → $dest"
    backup_then_rm "$dest"
  fi
  ln -s "$src" "$dest"
  success "Symlink → $dest"
}

unlink_if_managed() {
  local rel="$1" dest="$2"
  if [ -L "$dest" ]; then
    local cur want; cur="$(resolve_path "$dest")"; want="$(resolve_path "$DOTFILES_DIR/$rel")"
    if [ "$cur" = "$want" ]; then
      rm -f "$dest"
      success "Unlinked (disabled) → $dest"
    fi
  fi
}

# ====== ENABLED SET (newline list) ======
enabled_list=""

in_enabled() {
  # returns 0 if present
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
  info "Reading modules from $file"
  while IFS= read -r raw || [ -n "$raw" ]; do
    local line; line="$(trim_comment "$raw")"
    [ -z "$line" ] && continue
    case "$line" in
      '!'*) disable_mod "${line#\!}";;
      *)    enable_mod "$line";;
    esac
  done < "$file"
}

# ====== START ======
info "DOTFILES_DIR = $DOTFILES_DIR"
[ -d "$DOTFILES_DIR" ] || { error "DOTFILES_DIR not found"; exit 1; }

process_file "$DEFAULT_FILE"
process_file "$LOCAL_FILE"

info "Enabled modules list:"
printf '%s' "$enabled_list" | sed '/^$/d' | sort | sed 's/^/  - /' || true
echo

# ====== PARSE MODULE MAP ======
# Expand $HOME in destinations safely (no eval of random data)
MODULE_MAP=""
while IFS= read -r line || [ -n "$line" ]; do
  [ -z "$line" ] && continue
  IFS='|' read -r name rel dst_tpl <<<"$line"
  # expand literal $HOME tokens
  dst="${dst_tpl//\$HOME/$HOME}"
  MODULE_MAP+="${name}|${rel}|${dst}"$'\n'
done <<<"$MODULE_MAP_RAW"

# ====== APPLY ======
created=()
updated=()
unlinked=()
skipped_missing_src=()

info "Linking enabled modules…"
while IFS= read -r row || [ -n "$row" ]; do
  [ -z "$row" ] && continue
  IFS='|' read -r name rel dst <<<"$row"
  if in_enabled "$name"; then
    src="$DOTFILES_DIR/$rel"
    if [ ! -e "$src" ]; then
      warn "Missing source for enabled module '$name': $src"
      skipped_missing_src+=("$dst")
      continue
    fi
    if [ -L "$dst" ] && [ "$(resolve_path "$dst")" = "$(resolve_path "$src")" ]; then
      info "Up-to-date → $dst"
    else
      if [ -e "$dst" ] || [ -L "$dst" ]; then
        updated+=("$dst")
      else
        created+=("$dst")
      fi
      link_exact "$src" "$dst"
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
      localcur="$(resolve_path "$dst")"
      localwant="$(resolve_path "$DOTFILES_DIR/$rel")"
      if [ "$localcur" = "$localwant" ]; then
        rm -f "$dst"
        unlinked+=("$dst")
        success "Unlinked (disabled) → $dst"
      else
        info "Skip (not managed) → $dst"
      fi
    fi
  fi
done <<<"$MODULE_MAP"

# ====== EXTRAS ======
touch "$HOME/.hushlogin" && info "Ensured ~/.hushlogin"
if [ -x "$DOTFILES_DIR/after_setup.sh" ]; then
  info "Running after_setup.sh…"
  "$DOTFILES_DIR/after_setup.sh"
fi

# ====== SUMMARY ======
echo
log "========== SUMMARY =========="
[ "${#created[@]}" -gt 0 ]  && { log "Created:"; printf '  + %s\n' "${created[@]}"; }
[ "${#updated[@]}" -gt 0 ]  && { log "Updated:"; printf '  ~ %s\n' "${updated[@]}"; }
[ "${#unlinked[@]}" -gt 0 ] && { log "Unlinked:"; printf '  - %s\n' "${unlinked[@]}"; }
[ "${#skipped_missing_src[@]}" -gt 0 ] && { log "Skipped (missing src):"; printf '  ! %s\n' "${skipped_missing_src[@]}"; }
log "============================="
success "Done."
