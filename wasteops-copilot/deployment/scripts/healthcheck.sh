#!/bin/sh
set -eu
base_url="${1:-${WASTEOPS_BASE_URL:?set WASTEOPS_BASE_URL or pass URL}}"
curl --fail --silent --show-error --max-time 10 "$base_url/api/health/live" >/dev/null
curl --fail --silent --show-error --max-time 15 "$base_url/api/health/ready" >/dev/null
echo "WasteOps health checks passed"
