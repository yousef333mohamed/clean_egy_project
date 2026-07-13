#!/bin/sh
set -eu
: "${RESTORE_FILE:?required}" "${RESTORE_DATABASE_URL:?required}"
if [ "${CONFIRM_RESTORE:-}" != "RESTORE_WASTEOPS" ]; then
  echo "Refusing restore: set CONFIRM_RESTORE=RESTORE_WASTEOPS" >&2
  exit 2
fi
input="$RESTORE_FILE"
temporary=""
case "$input" in
  *.age) : "${AGE_IDENTITY_FILE:?required}"; temporary="$(mktemp)"; trap 'rm -f "$temporary"' EXIT; age --decrypt -i "$AGE_IDENTITY_FILE" -o "$temporary" "$input"; input="$temporary" ;;
esac
pg_restore --exit-on-error --clean --if-exists --no-owner --no-acl --dbname="$RESTORE_DATABASE_URL" "$input"
psql "$RESTORE_DATABASE_URL" -v ON_ERROR_STOP=1 -c 'SELECT count(*) FROM alembic_version' >/dev/null
echo "Restore and basic verification completed"
