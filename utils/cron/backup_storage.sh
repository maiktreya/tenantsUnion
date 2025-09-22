#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
SOURCE_DIR="${PROJECT_ROOT}/storage"
BACKUP_ROOT="${HOME}/back"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_FILE="${BACKUP_ROOT}/storage-${TIMESTAMP}.tar.gz"

if [[ ! -d "$SOURCE_DIR" ]]; then
  echo "Source directory '$SOURCE_DIR' does not exist." >&2
  exit 1
fi

mkdir -p "$BACKUP_ROOT"

tar -czf "$BACKUP_FILE" -C "$PROJECT_ROOT" "$(basename "$SOURCE_DIR")"
echo "Backup written to ${BACKUP_FILE}"

cd "$BACKUP_ROOT"
ls -1t storage-*.tar.gz | tail -n +3 | xargs -r rm --
