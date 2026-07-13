"""Run fake/recorded/live evaluation suites and enforce deterministic quality gates."""

import argparse
import asyncio
from pathlib import Path

from app.core.database import AsyncSessionLocal
from app.evaluation.enums import EvaluationMode
from app.evaluation.quality_gate import QualityGate
from app.evaluation.regression_runner import RegressionRunner


async def main(args) -> bool:
    paths = sorted(Path("evaluation_datasets").glob("*/*.json")) if args.all else [Path(args.dataset)]
    aggregate: dict[str, list[float]] = {}
    total = critical = 0
    async with AsyncSessionLocal() as session:
        for path in paths:
            run = await RegressionRunner(session).run(path, mode=EvaluationMode(args.mode), prompt_overrides=dict(item.split("=", 1) for item in args.prompt))
            total += len(run.results)
            critical += run.critical_failures
            for key, value in run.metrics.items():
                aggregate.setdefault(key, []).append(value)
            print(f"{path}: {sum(item.passed for item in run.results)}/{len(run.results)} passed; run={run.run_id}")
    metrics = {key: sum(values) / len(values) for key, values in aggregate.items()}
    if len(paths) == 1 and paths[0].parent.name == "safety":
        passed = critical == 0 and all(result.passed for result in run.results)
        print(f"Safety gate: {'PASS' if passed else 'FAIL'}; critical_failures={critical}")
        return passed
    gate = QualityGate().evaluate(metrics, total_cases=total, critical_failures=critical)
    print(f"Quality gate: {'PASS' if gate.passed else 'FAIL'}; critical_failures={critical}")
    return gate.passed


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--dataset")
    parser.add_argument("--mode", choices=[item.value for item in EvaluationMode], default=EvaluationMode.FAKE_PROVIDERS.value)
    parser.add_argument("--prompt", action="append", default=[], metavar="KEY=VERSION")
    raise SystemExit(0 if asyncio.run(main(parser.parse_args())) else 1)
