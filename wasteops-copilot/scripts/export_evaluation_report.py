"""Export an existing immutable evaluation report in JSON or Markdown."""

import argparse
from pathlib import Path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    args = parser.parse_args()
    suffix = "md" if args.format == "markdown" else "json"
    path = Path("evaluation_reports") / f"{args.run_id}.{suffix}"
    if not path.is_file():
        raise SystemExit(f"Report not found: {path}")
    print(path.read_text(encoding="utf-8"))
