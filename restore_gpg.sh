#!/bin/bash

# Check if a file was provided
if [ -z "$1" ]; then
    echo "Usage: $0 <path_to_backup_file.tar.gz>"
    exit 1
fi

BACKUP_FILE=$1
TEMP_DIR=$(mktemp -d)

echo "Starting GPG restore from $BACKUP_FILE..."

# Extract the archive
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# 1. Import Public Keys
gpg --import "$TEMP_DIR/pubkeys.gpg"

# 2. Import Private Keys
gpg --import "$TEMP_DIR/privkeys.gpg"

# 3. Import Trust Database
gpg --import-ownertrust "$TEMP_DIR/ownertrust.txt"

# Cleanup
rm -rf "$TEMP_DIR"

echo "---------------------------------------------------"
echo "Restore complete."
echo "Verify your keys using: gpg --list-secret-keys"
echo "---------------------------------------------------"
