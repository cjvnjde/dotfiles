#!/bin/bash

echo "Updating main repository..."
git pull

echo "Updating submodules..."
git submodule update --init --recursive

echo "Updating and checking out submodules to main branch..."
git submodule foreach --recursive '
    git pull origin main
    git checkout main
'

echo "All submodules updated and checked out to main branch."

