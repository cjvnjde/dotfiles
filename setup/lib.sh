#!/usr/bin/env bash

log() {
  printf '%s\n' "$*"
}

info() {
  printf '[INFO] %s\n' "$*"
}

warn() {
  printf '[WARN] %s\n' "$*" >&2
}

error() {
  printf '[ERR ] %s\n' "$*" >&2
}

success() {
  printf '[ OK ] %s\n' "$*"
}

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

backup_path() {
  local target="$1"
  local backup="$target.bak"
  local counter=1

  [ -e "$target" ] || [ -L "$target" ] || return 0

  while [ -e "$backup" ] || [ -L "$backup" ]; do
    backup="$target.bak$counter"
    counter=$((counter + 1))
  done

  mv "$target" "$backup"
  info "Backup → $backup"
}

ensure_directory() {
  local dir="$1"

  if [ -d "$dir" ] && [ ! -L "$dir" ]; then
    return 0
  fi

  if [ -e "$dir" ] || [ -L "$dir" ]; then
    backup_path "$dir"
  fi

  mkdir -p "$dir"
}

is_link_to() {
  local src="$1"
  local dest="$2"
  local current_resolved
  local src_resolved

  [ -L "$dest" ] || return 1

  current_resolved="$(resolve_path "$dest")"
  src_resolved="$(resolve_path "$src")"

  [ "$current_resolved" = "$src_resolved" ]
}

LINK_WAS_CHANGED=0
link_exact() {
  local src="$1"
  local dest="$2"

  LINK_WAS_CHANGED=0

  if [ ! -e "$src" ]; then
    warn "Source missing: $src"
    return 1
  fi

  mkdir -p "$(dirname "$dest")"

  if is_link_to "$src" "$dest"; then
    return 0
  fi

  if [ -e "$dest" ] || [ -L "$dest" ]; then
    backup_path "$dest"
  fi

  ln -s "$src" "$dest"
  LINK_WAS_CHANGED=1
}

UNLINK_WAS_CHANGED=0
unlink_managed() {
  local src="$1"
  local dest="$2"

  UNLINK_WAS_CHANGED=0

  if ! is_link_to "$src" "$dest"; then
    return 1
  fi

  rm -f "$dest"
  UNLINK_WAS_CHANGED=1
}

link_path() {
  local src="$1"
  local dest="$2"

  if link_exact "$src" "$dest" && [ "$LINK_WAS_CHANGED" -eq 1 ]; then
    success "Linked → $dest"
  fi
}

unlink_path() {
  local src="$1"
  local dest="$2"

  if unlink_managed "$src" "$dest" && [ "$UNLINK_WAS_CHANGED" -eq 1 ]; then
    success "Unlinked → $dest"
  fi
}

read_value_file() {
  local path="$1"
  local default_value="${2:-}"
  local raw
  local line

  if [ -f "$path.local" ]; then
    path="$path.local"
  elif [ ! -f "$path" ]; then
    printf '%s\n' "$default_value"
    return 0
  fi

  while IFS= read -r raw || [ -n "$raw" ]; do
    line="$(trim_comment "$raw")"
    [ -n "$line" ] || continue
    printf '%s\n' "$line"
    return 0
  done < "$path"

  printf '%s\n' "$default_value"
}

rmdir_if_empty() {
  local dir="$1"

  [ -d "$dir" ] || return 0
  rmdir "$dir" 2>/dev/null || true
}
