#!/bin/sh
set -eu
: "${BACKUP_DIRECTORY:?required}"
: "${BACKUP_RETENTION_DAYS:=30}"
: "${PGHOST:?required}" "${PGDATABASE:?required}" "${PGUSER:?required}" "${PGPASSFILE:?required}"
umask 077
mkdir -p "$BACKUP_DIRECTORY"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
plain="$BACKUP_DIRECTORY/wasteops-$stamp.dump"
pg_dump --format=custom --no-owner --no-acl --file="$plain" "$PGDATABASE"
artifact="$plain"
if [ "${BACKUP_ENCRYPTION_ENABLED:-true}" = true ]; then
  : "${AGE_RECIPIENT:?AGE_RECIPIENT is required for encrypted backups}"
  age --recipient "$AGE_RECIPIENT" --output "$plain.age" "$plain"
  rm -f "$plain"
  artifact="$plain.age"
fi
sha256sum "$artifact" >"$artifact.sha256"
find "$BACKUP_DIRECTORY" -type f -name 'wasteops-*' -mtime "+$BACKUP_RETENTION_DAYS" -delete
echo "Backup completed: $(basename "$artifact")"
