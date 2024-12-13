#!/bin/bash

echo "Updating main repository..."
git pull

echo "Updating submodules..."
git submodule update --init --recursive

# Get the current branch of the main repository
main_branch=$(git rev-parse --abbrev-ref HEAD)
echo "Main repository branch: $main_branch"

export main_branch=$main_branch

echo "Updating and checking out submodules to matching branch if possible, otherwise to main..."
git submodule foreach --recursive '
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

echo "All submodules updated and checked out to the $main_branch branch if possible, otherwise main."

