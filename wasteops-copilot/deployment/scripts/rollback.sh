#!/bin/sh
set -eu
: "${ROLLBACK_IMAGE_TAG:?previous immutable image tag required}"
: "${WASTEOPS_BASE_URL:?required}"
export IMAGE_TAG="$ROLLBACK_IMAGE_TAG"
compose_file="${COMPOSE_FILE:-deployment/compose/compose.production.yml}"
# Application rollback only. Database downgrades require a separate reviewed recovery plan.
docker compose -f "$compose_file" pull frontend backend worker
docker compose -f "$compose_file" up -d --no-deps frontend backend worker
"$(dirname "$0")/healthcheck.sh" "$WASTEOPS_BASE_URL"
