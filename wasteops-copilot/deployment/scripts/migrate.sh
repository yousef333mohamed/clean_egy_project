#!/bin/sh
set -eu
compose_file="${COMPOSE_FILE:-deployment/compose/compose.production.yml}"
docker compose -f "$compose_file" --profile tools run --rm migration alembic current
docker compose -f "$compose_file" --profile tools run --rm migration alembic upgrade head
docker compose -f "$compose_file" --profile tools run --rm migration alembic current
