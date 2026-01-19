#!/bin/bash

# Check if Key ID is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <GPG_KEY_ID>"
    echo "Hint: Run 'gpg --list-secret-keys --keyid-format LONG' to find your ID."
    exit 1
fi

SIGN_KEY=$1
BACKUP_DIR="$HOME/gpg_backups"
DATE=$(date +%Y-%m-%d)
FILENAME="gpg-backup-$SIGN_KEY-$DATE.tar.gz"
TEMP_DIR=$(mktemp -d)

mkdir -p "$BACKUP_DIR"

echo "Starting GPG backup for key: $SIGN_KEY..."

# 1. Export Specific Public Key
gpg --export --export-options backup --output "$TEMP_DIR/pubkeys.gpg" "$SIGN_KEY"

# 2. Export Specific Private Key
gpg --export-secret-keys --export-options backup --output "$TEMP_DIR/privkeys.gpg" "$SIGN_KEY"

# 3. Export Trust Database (Trust is global, but essential for the key to work)
gpg --export-ownertrust > "$TEMP_DIR/ownertrust.txt"

# Create the archive
tar -czf "$BACKUP_DIR/$FILENAME" -C "$TEMP_DIR" .

# Cleanup
rm -rf "$TEMP_DIR"

echo "---------------------------------------------------"
echo "Backup complete: $BACKUP_DIR/$FILENAME"
echo "---------------------------------------------------"
