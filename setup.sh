#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

resolve_script_path() {
  local path="$1"

  if command -v realpath >/dev/null 2>&1; then
    realpath "$path" 2>/dev/null && return
  fi

  if command -v readlink >/dev/null 2>&1; then
    readlink -f "$path" 2>/dev/null && return
  fi

  local dir
  dir="$(cd -P "$(dirname "$path")" && pwd)"
  printf '%s/%s\n' "$dir" "$(basename "$path")"
}

SCRIPT_PATH="$(resolve_script_path "${BASH_SOURCE[0]}")"
ROOT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd -P)"
DEFAULT_FILE="$ROOT_DIR/.modules"
LOCAL_FILE="$ROOT_DIR/.modules.local"

action_failed() {
  error "Failed at line $1: $2"
}

source "$ROOT_DIR/setup/lib.sh"
trap 'action_failed "$LINENO" "$BASH_COMMAND"' ERR

export DOTFILES_DIR="$ROOT_DIR"
exec 3<&0

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
  local raw
  local line

  [ -f "$file" ] || return 0

  info "Reading modules from: $file"

  while IFS= read -r raw || [ -n "$raw" ]; do
    line="$(trim_comment "$raw")"
    [ -n "$line" ] || continue

    case "$line" in
      '!'*) disable_mod "${line#\!}" ;;
      *)    enable_mod "$line" ;;
    esac
  done < "$file"
}

discover_modules() {
  local path
  local name
  local module_scripts=""

  for path in "$ROOT_DIR"/*/setup.sh; do
    [ -f "$path" ] || continue
    name="$(basename "$(dirname "$path")")"
    module_scripts="${module_scripts}${name}|${path}"$'\n'
  done

  for path in "$ROOT_DIR"/home/setup/*.sh; do
    [ -f "$path" ] || continue
    name="$(basename "$path" .sh)"
    module_scripts="${module_scripts}${name}|${path}"$'\n'
  done

  printf '%s' "$module_scripts" | sort
}

module_exists() {
  local name="$1"
  local row_name
  local _unused

  while IFS='|' read -r row_name _unused || [ -n "${row_name:-}" ]; do
    [ -n "${row_name:-}" ] || continue
    [ "$row_name" = "$name" ] && return 0
  done <<< "$MODULE_SCRIPTS"

  return 1
}

info "DOTFILES_DIR = $ROOT_DIR"
process_file "$DEFAULT_FILE"
process_file "$LOCAL_FILE"

info "Enabled modules:"
if [ -n "$enabled_list" ]; then
  printf '%s' "$enabled_list" | sed '/^$/d' | sort | sed 's/^/  - /'
else
  echo "  (none)"
fi
echo

MODULE_SCRIPTS="$(discover_modules)"

while IFS= read -r name || [ -n "${name:-}" ]; do
  [ -n "${name:-}" ] || continue
  if ! module_exists "$name"; then
    warn "Unknown module: $name"
  fi
done <<< "$(printf '%s' "$enabled_list" | sed '/^$/d' | sort -u)"

while IFS='|' read -r name script || [ -n "${name:-}" ]; do
  [ -n "${name:-}" ] || continue

  if in_enabled "$name"; then
    info "Enable $name"
    bash "$script" enable <&3
  else
    bash "$script" disable <&3
  fi
done <<< "$MODULE_SCRIPTS"

touch "$HOME/.hushlogin" 2>/dev/null && info "Ensured ~/.hushlogin"

if [ -f "$ROOT_DIR/after_setup.sh" ]; then
  info "Running after_setup.sh…"
  bash "$ROOT_DIR/after_setup.sh"
fi

exec 3<&-
success "Done."
