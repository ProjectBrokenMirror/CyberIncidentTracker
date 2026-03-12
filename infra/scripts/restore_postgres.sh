#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL is required (postgresql://...)." >&2
  exit 1
fi

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <backup_file.dump>" >&2
  exit 1
fi

BACKUP_FILE="$1"
if [[ ! -f "${BACKUP_FILE}" ]]; then
  echo "Backup file not found: ${BACKUP_FILE}" >&2
  exit 1
fi

echo "Restoring backup: ${BACKUP_FILE}"
pg_restore --clean --if-exists --no-owner --no-privileges --dbname="${DATABASE_URL}" "${BACKUP_FILE}"
echo "Restore complete."
