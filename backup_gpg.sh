#!/bin/bash

# Configuration
BACKUP_DIR="$HOME/gpg_backups"
DATE=$(date +%Y-%m-%d)
FILENAME="gpg-backup-$DATE.tar.gz"
TEMP_DIR=$(mktemp -d)

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "Starting GPG backup..."

# 1. Export Public Keys
gpg --export --export-options backup --output "$TEMP_DIR/pubkeys.gpg"

# 2. Export Private Keys (This will prompt for your passphrase)
gpg --export-secret-keys --export-options backup --output "$TEMP_DIR/privkeys.gpg"

# 3. Export Trust Database
gpg --export-ownertrust > "$TEMP_DIR/ownertrust.txt"

# Create the tar.gz archive
tar -czf "$BACKUP_DIR/$FILENAME" -C "$TEMP_DIR" .

# Cleanup
rm -rf "$TEMP_DIR"

echo "---------------------------------------------------"
echo "Backup complete: $BACKUP_DIR/$FILENAME"
echo "IMPORTANT: Store this file in a secure, encrypted location."
echo "---------------------------------------------------"

