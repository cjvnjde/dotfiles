#!/bin/bash

IGNORE_DIR="test"

echo "Updating main repository..."
git pull

echo "Updating submodules..."
git submodule update --init --recursive

main_branch=$(git rev-parse --abbrev-ref HEAD)
echo "Main repository branch: $main_branch"

export main_branch=$main_branch
export IGNORE_DIR=$IGNORE_DIR

echo "Updating and checking out submodules (ignoring '$IGNORE_DIR')..."

git submodule foreach --recursive '
    # Check if the submodule path starts with the ignored directory
    if [[ "$path" == "$IGNORE_DIR"* ]]; then
        echo "  [Skipping] Submodule $name is inside ignored folder: $IGNORE_DIR"
        exit 0
    fi

    git fetch origin

    if git show-ref -q --verify refs/remotes/origin/"$main_branch"; then
      echo "  Trying to checkout branch: $main_branch"
      git checkout "$main_branch" 2>/dev/null
      if [ $? -ne 0 ]; then
        echo "  Failed to checkout $main_branch, falling back to main"
        git checkout main 2>/dev/null
      fi 
      git reset --hard origin/"$main_branch" 2>/dev/null
      if [ $? -ne 0 ]; then
        echo "  Failed to reset to origin/$main_branch, falling back to origin/main"
        git reset --hard origin/main 2>/dev/null
      fi 
    else
      echo "  Branch $main_branch not found, falling back to main"
      git checkout main 2>/dev/null
      git reset --hard origin/main 2>/dev/null
    fi
'

echo "All submodules updated (excluding '$IGNORE_DIR')."
