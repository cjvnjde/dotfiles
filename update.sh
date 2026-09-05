#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/setup/parallel.sh"
parallel_init

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
# Add folder names or paths to ignore (space-separated)
IGNORE_DIRS=("test" "tests")

# ──────────────────────────────────────────────
# Colors
# ──────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${RESET}  $*"; }
log_ok()    { echo -e "${GREEN}[OK]${RESET}    $*"; }
log_skip()  { echo -e "${YELLOW}[SKIP]${RESET}  $*"; }
log_err()   { echo -e "${RED}[ERR]${RESET}   $*"; }
log_head()  { echo -e "\n${BOLD}${CYAN}── $* ──${RESET}\n"; }

# ──────────────────────────────────────────────
# Pre-flight checks
# ──────────────────────────────────────────────
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    log_err "Not inside a git repository."
    exit 1
fi

# ──────────────────────────────────────────────
# Step 1 — Pull main repository
# ──────────────────────────────────────────────
log_head "Updating main repository"

main_branch=$(git rev-parse --abbrev-ref HEAD)
log_info "Current branch: ${BOLD}$main_branch${RESET}"

if ! git pull --no-recurse-submodules; then
    log_err "Failed to pull main repository."
    exit 1
fi
log_ok "Main repository up to date."

# ──────────────────────────────────────────────
# Step 2 — Update submodules in parent-first waves
# ──────────────────────────────────────────────
should_ignore() {
    local sm_path="$1"
    local dir
    for dir in "${IGNORE_DIRS[@]}"; do
        if [[ "$sm_path" == "$dir" ||
              "$sm_path" == "$dir/"* ||
              "$sm_path" == *"/$dir" ||
              "$sm_path" == *"/$dir/"* ]]; then
            return 0
        fi
    done
    return 1
}

update_submodule() (
    local parent="$1"
    local child="$2"
    local sm_path="$3"
    local name="$4"
    local status_file="$5"
    local directory="$parent/$child"

    if [ ! -e "$directory/.git" ]; then
        if ! git -C "$parent" -c submodule.recurse=false -c fetch.recurseSubmodules=false submodule update -- "$child"; then
            log_err "Failed to initialise $sm_path."
            return 1
        fi
    fi

    if should_ignore "$sm_path"; then
        log_skip "$sm_path (inside ignored folder)"
        printf 'skipped\n' > "$status_file"
        return 0
    fi

    log_info "Updating $name ($sm_path) ..."
    if ! cd -- "$directory"; then
        log_err "Failed to enter $sm_path."
        return 1
    fi
    if ! git -c submodule.recurse=false switch main; then
        log_err "Failed to switch $sm_path to main."
        return 1
    fi
    if ! git -c submodule.recurse=false pull --no-recurse-submodules; then
        log_err "Failed to pull $sm_path."
        return 1
    fi

    printf 'updated\n' > "$status_file"
    log_ok "$sm_path → main"
)

log_head "Updating submodules (ignoring: ${IGNORE_DIRS[*]})"

repo_root=$(git rev-parse --show-toplevel)
status_dir=$(mktemp -d)
trap 'parallel_cleanup; rm -rf -- "$status_dir"' EXIT
parents=("$repo_root")
worker_count=0
update_failed=0

while [ "${#parents[@]}" -gt 0 ]; do
    next_parents=()
    next_status_files=()
    next_count=0
    for parent in "${parents[@]}"; do
        if [ ! -e "$parent/.gitmodules" ]; then
            continue
        fi
        # Register all siblings before workers can clone them or touch shared config.
        if ! git -C "$parent" submodule init; then
            log_err "Failed to register submodules in $parent."
            update_failed=1
            continue
        fi
        # An empty config has no children; malformed or unreadable configs are errors.
        if git config --null --file "$parent/.gitmodules" --get-regexp '^submodule\..*\.path$' > "$status_dir/children"; then
            :
        else
            config_status=$?
            if [ "$config_status" -eq 1 ]; then
                continue
            fi
            log_err "Failed to discover submodules in $parent."
            update_failed=1
            continue
        fi
        while IFS= read -r -d '' record <&3; do
            key="${record%%$'\n'*}"
            child="${record#*$'\n'}"
            name="${key#submodule.}"
            name="${name%.path}"
            directory="$parent/$child"
            sm_path="${directory#"$repo_root"/}"
            worker_count=$((worker_count + 1))
            status_file="$status_dir/$worker_count"
            # A worker must explicitly record success; early exits remain failures.
            printf 'failed\n' > "$status_file"
            parallel_run "$sm_path" update_submodule "$parent" "$child" "$sm_path" "$name" "$status_file" 3<&-
            next_parents[next_count]="$directory"
            next_status_files[next_count]="$status_file"
            next_count=$((next_count + 1))
        done 3< "$status_dir/children"
    done
    if ! parallel_wait; then
        update_failed=1
    fi
    if [ "$next_count" -eq 0 ]; then
        break
    fi
    parents=()
    for ((index=0; index<next_count; index++)); do
        read -r status < "${next_status_files[index]}"
        if [[ "$status" == updated || "$status" == skipped ]]; then
            parents+=("${next_parents[index]}")
        fi
    done
done

# ──────────────────────────────────────────────
# Step 3 — Summary
# ──────────────────────────────────────────────
updated=0
skipped=0
failed=0
for ((worker=1; worker<=worker_count; worker++)); do
    read -r status < "$status_dir/$worker"
    case "$status" in
        updated) updated=$((updated + 1)) ;;
        skipped) skipped=$((skipped + 1)) ;;
        *) failed=$((failed + 1)) ;;
    esac
done

log_head "Summary"
echo -e "  ${GREEN}Updated :${RESET} $updated"
echo -e "  ${YELLOW}Skipped :${RESET} $skipped"
echo -e "  ${RED}Failed  :${RESET} $failed"
echo ""

if [ "$failed" -gt 0 ] || [ "$update_failed" -ne 0 ]; then
    log_err "Some submodules failed to update or could not be discovered. Check the output above."
    exit 1
fi

log_ok "All done."
