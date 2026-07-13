"""Refuses metric claims without a labeled evaluation dataset."""

import argparse
from pathlib import Path
from training.train_overflow import train


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--overflow-dataset", type=Path, required=True)
    args = parser.parse_args()
    _, metrics = train(args.overflow_dataset, 24)
    print(metrics)


if __name__ == "__main__":
    main()
