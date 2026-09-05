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

if ! git pull; then
    log_err "Failed to pull main repository."
    exit 1
fi
log_ok "Main repository up to date."

# ──────────────────────────────────────────────
# Step 2 — Init submodules
# ──────────────────────────────────────────────
log_head "Initialising submodules"
if ! git submodule update --init --recursive --jobs "$PARALLEL_JOBS"; then
    log_err "Failed to initialise submodules."
    exit 1
fi
log_ok "Submodules initialised."

# ──────────────────────────────────────────────
# Step 3 — Update submodules in parent-first waves
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
    local directory="$1"
    local sm_path="$2"
    local name="$3"
    local status_file="$4"
    local target_branch="" candidate

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
    if ! git fetch origin --prune; then
        log_err "Failed to fetch $sm_path."
        return 1
    fi

    for candidate in "$main_branch" "main" "master"; do
        if git show-ref -q --verify "refs/remotes/origin/$candidate"; then
            target_branch="$candidate"
            break
        fi
    done

    if [ -z "$target_branch" ]; then
        if ! target_branch=$(git remote show origin 2>/dev/null | sed -n "s/.*HEAD branch: //p"); then
            log_err "Failed to discover the origin HEAD branch for $sm_path."
            return 1
        fi
    fi
    if [ -z "$target_branch" ]; then
        log_err "Could not determine a target branch for $sm_path."
        return 1
    fi

    if ! git checkout "$target_branch" 2>/dev/null; then
        log_err "Failed to checkout $target_branch in $sm_path."
        return 1
    fi
    if ! git reset --hard "origin/$target_branch" 2>/dev/null; then
        log_err "Failed to reset $sm_path to origin/$target_branch."
        return 1
    fi

    printf 'updated\n' > "$status_file"
    log_ok "$sm_path → $target_branch"
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
    next_count=0
    for parent in "${parents[@]}"; do
        # Enumerate only immediate children, after this parent has finished updating.
        # Git supplies these variables in the child shell.
        # shellcheck disable=SC2016
        if ! git -C "$parent" submodule foreach --quiet 'printf "%s\000%s\000" "$name" "$sm_path"' > "$status_dir/children"; then
            log_err "Failed to discover submodules in $parent."
            update_failed=1
            continue
        fi
        while IFS= read -r -d '' name <&3 && IFS= read -r -d '' child <&3; do
            directory="$parent/$child"
            sm_path="${directory#"$repo_root"/}"
            worker_count=$((worker_count + 1))
            status_file="$status_dir/$worker_count"
            # A worker must explicitly record success; early exits remain failures.
            printf 'failed\n' > "$status_file"
            parallel_run "$sm_path" update_submodule "$directory" "$sm_path" "$name" "$status_file" 3<&-
            next_parents[next_count]="$directory"
            next_count=$((next_count + 1))
        done 3< "$status_dir/children"
    done
    if ! parallel_wait; then
        update_failed=1
    fi
    if [ "$next_count" -eq 0 ]; then
        break
    fi
    parents=("${next_parents[@]}")
done

# ──────────────────────────────────────────────
# Step 4 — Summary
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
