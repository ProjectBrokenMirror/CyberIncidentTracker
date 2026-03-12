#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL is required (postgresql://...)." >&2
  exit 1
fi

BACKUP_DIR="${1:-./backups}"
mkdir -p "${BACKUP_DIR}"
TIMESTAMP="$(date +"%Y%m%d-%H%M%S")"
BACKUP_FILE="${BACKUP_DIR}/incident-tracker-${TIMESTAMP}.dump"

echo "Creating backup: ${BACKUP_FILE}"
pg_dump --format=custom --file="${BACKUP_FILE}" "${DATABASE_URL}"
echo "Backup complete."
