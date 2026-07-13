import argparse, json
from dataclasses import asdict
from pathlib import Path
import pandas as pd
from app.monitoring.drift_monitor import compare


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("artifacts/reports/drift/latest.json"))
    args = parser.parse_args()
    signals = compare(pd.read_parquet(args.reference), pd.read_parquet(args.current))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {
                "drift_detected": any(s.drift_detected for s in signals),
                "features": [asdict(s) for s in signals],
                "recommendation": "REVIEW_MODEL" if any(s.drift_detected for s in signals) else "CONTINUE_MONITORING",
            },
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
