#!/usr/bin/env bash
set -euo pipefail
# backup_storage.sh
# Daily backup of the tenantsUnion storage directory.
# Include as crontab -e: 0 2 * * * $HOME/github/prod/tenantsUnion/utils/cron/backup_storage.sh

# Explicit paths for cron reliability
: "${HOME:?HOME is not set — aborting}"
PROJECT_DIR="${HOME}/github/prod/tenantsUnion"
SOURCE_DIR="${PROJECT_DIR}/storage"
BACKUP_ROOT="${HOME}/back"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_FILE="${BACKUP_ROOT}/storage-${TIMESTAMP}.tar.gz"

# Verify source directory exists
if [[ ! -d "$SOURCE_DIR" ]]; then
  echo "Source directory '$SOURCE_DIR' does not exist." >&2
  exit 1
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_ROOT"

# Create backup (tar from parent directory to avoid path issues)
tar -czf "$BACKUP_FILE" -C "$PROJECT_DIR" "storage"
echo "Backup written to ${BACKUP_FILE}"

# Clean up old backups (keep only 2 most recent)
cd "$BACKUP_ROOT"
ls -1t storage-*.tar.gz 2>/dev/null | tail -n +3 | xargs -r rm --
