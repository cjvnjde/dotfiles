#!/bin/bash

echo "Updating main repository..."
git pull

echo "Updating submodules..."
git submodule update --init --recursive

echo "Updating and checking out submodules to main branch..."
git submodule foreach --recursive '
    git fetch origin
    branch=$(git symbolic-ref --short HEAD 2>/dev/null)
    if [ "$branch" != "main" ]; then
        git checkout main
    fi
    git reset --hard origin/main
'

echo "All submodules updated and checked out to main branch."

