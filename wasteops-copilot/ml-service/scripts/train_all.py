"""Explicit orchestration that requires prepared, versioned datasets."""

import argparse
from pathlib import Path
from training.train_overflow import train


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-directory", type=Path, required=True)
    args = parser.parse_args()
    overflow = args.dataset_directory / "overflow_features.csv"
    if not overflow.is_file():
        parser.error("Prepared point-in-time overflow_features.csv is required; raw future-leaking data is not accepted")
    _, metrics = train(overflow, 24)
    print({"bin-overflow": metrics, "other_models": "Require their own prepared, reviewed target datasets"})


if __name__ == "__main__":
    main()
