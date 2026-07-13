"""Production-mode smoke checks without mandatory live model calls."""

import argparse
import os
import sys
import urllib.error
import urllib.request


def request(base: str, path: str, token: str = "") -> tuple[int, str]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urllib.request.urlopen(urllib.request.Request(base.rstrip("/") + path, headers=headers), timeout=20) as response:
            return response.status, response.read(200_000).decode()
    except urllib.error.HTTPError as error:
        return error.code, error.read(20_000).decode()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--fixture-mode", action="store_true")
    args = parser.parse_args()
    token = os.getenv("SMOKE_ACCESS_TOKEN", "")
    checks = [("/api/health/live", {200}), ("/api/health/ready", {200}), ("/api/health/version", {200})]
    checks.append(("/api/auth/me", {200} if token else {401}))
    if token:
        checks.extend((path, {200, 403, 422, 503}) for path in ("/api/analytics/tools", "/api/decisions/types", "/api/documents"))
    failures = []
    for path, expected in checks:
        status, body = request(args.base_url, path, token)
        if status not in expected or "embedding" in body.lower() and "[" in body:
            failures.append(f"{path}: status {status}")
    if failures:
        print("Smoke failures: " + "; ".join(failures), file=sys.stderr)
        return 1
    print("Production smoke checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
