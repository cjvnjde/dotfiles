#!/bin/bash
set -euo pipefail

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
git submodule update --init --recursive
log_ok "Submodules initialised."

# ──────────────────────────────────────────────
# Step 3 — Build the ignore pattern and export
# ──────────────────────────────────────────────
# We pass the list as a single delimited string so the
# subshell spawned by `git submodule foreach` can read it.
IGNORE_DIRS_JOINED=$(IFS="|"; echo "${IGNORE_DIRS[*]}")

export main_branch
export IGNORE_DIRS_JOINED

# Counters (temp file because foreach runs in subshells)
COUNTER_FILE=$(mktemp)
echo "0 0 0" > "$COUNTER_FILE"          # updated  skipped  failed
export COUNTER_FILE

# ──────────────────────────────────────────────
# Step 4 — Update each submodule
# ──────────────────────────────────────────────
log_head "Updating submodules (ignoring: ${IGNORE_DIRS[*]})"

git submodule foreach --recursive '
    # ── helper: should this path be ignored? ──
    should_ignore() {
        local sm_path="$1"
        IFS="|" read -ra dirs <<< "$IGNORE_DIRS_JOINED"
        for dir in "${dirs[@]}"; do
            # Match: exact name, leading component, or anywhere in path
            if [[ "$sm_path" == "$dir"      ||
                  "$sm_path" == "$dir/"*     ||
                  "$sm_path" == *"/$dir"     ||
                  "$sm_path" == *"/$dir/"*   ]]; then
                return 0
            fi
        done
        return 1
    }

    # ── helper: increment counter ──
    bump() {
        # $1 = field index (1=updated 2=skipped 3=failed)
        read -r u s f < "$COUNTER_FILE"
        case $1 in
            1) u=$((u+1)) ;; 2) s=$((s+1)) ;; 3) f=$((f+1)) ;;
        esac
        echo "$u $s $f" > "$COUNTER_FILE"
    }

    # ── ignore check ──
    if should_ignore "$path"; then
        echo -e "\033[0;33m[SKIP]\033[0m  $name  (inside ignored folder)"
        bump 2
        exit 0
    fi

    echo -e "\033[0;34m[INFO]\033[0m  Updating $name ($path) ..."
    git fetch origin --prune

    # Determine the best branch: prefer $main_branch, fall back to main, then default remote HEAD
    target_branch=""
    for candidate in "$main_branch" "main" "master"; do
        if git show-ref -q --verify "refs/remotes/origin/$candidate"; then
            target_branch="$candidate"
            break
        fi
    done

    if [ -z "$target_branch" ]; then
        # Last resort: whatever HEAD points to on origin
        target_branch=$(git remote show origin 2>/dev/null | sed -n "s/.*HEAD branch: //p")
    fi

    if [ -z "$target_branch" ]; then
        echo -e "\033[0;31m[ERR]\033[0m   Could not determine a target branch for $name"
        bump 3
        exit 0   # do not abort the whole loop
    fi

    if git checkout "$target_branch" 2>/dev/null; then
        git reset --hard "origin/$target_branch" 2>/dev/null
        echo -e "\033[0;32m[OK]\033[0m    $name → $target_branch"
        bump 1
    else
        echo -e "\033[0;31m[ERR]\033[0m   Failed to checkout $target_branch in $name"
        bump 3
    fi
'

# ──────────────────────────────────────────────
# Step 5 — Summary
# ──────────────────────────────────────────────
read -r updated skipped failed < "$COUNTER_FILE"
rm -f "$COUNTER_FILE"

log_head "Summary"
echo -e "  ${GREEN}Updated :${RESET} $updated"
echo -e "  ${YELLOW}Skipped :${RESET} $skipped"
echo -e "  ${RED}Failed  :${RESET} $failed"
echo ""

if [ "$failed" -gt 0 ]; then
    log_err "Some submodules failed to update. Check the output above."
    exit 1
fi

log_ok "All done."
