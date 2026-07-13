#!/bin/sh
set -eu
: "${IMAGE_TAG:?immutable IMAGE_TAG is required}"
compose_file="${COMPOSE_FILE:-deployment/compose/compose.production.yml}"
docker compose -f "$compose_file" config --quiet
docker compose -f "$compose_file" pull
"$(dirname "$0")/migrate.sh"
docker compose -f "$compose_file" up -d --remove-orphans
"$(dirname "$0")/healthcheck.sh" "${WASTEOPS_BASE_URL:?required}"
