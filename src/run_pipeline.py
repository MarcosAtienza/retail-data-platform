"""Run the local Olist pipeline from raw CSVs through Gold analytics.

Usage (from the project root):
    python src/run_pipeline.py

Stages:
    1. Raw CSV -> Bronze Parquet
    2. Bronze Parquet -> Silver Parquet
    3. Validate 31 data-quality rules and generate a CSV report
    4. Build the Gold analytical models
    5. Run Gold integrity checks and business SQL queries

A nonzero exit code stops execution. Quality warnings are permitted; a
quality ERROR failure or a nonzero Gold integrity check stops the pipeline.
"""

from pathlib import Path
import subprocess
import sys
from time import perf_counter


PROJECT_ROOT = Path(__file__).resolve().parent.parent

STAGES = (
    ("Bronze ingestion", "src/ingest_bronze.py"),
    ("Silver transformations", "src/transform_silver.py"),
    ("Data-quality validation and CSV report", "src/generate_quality_report.py"),
    ("Gold analytical models", "src/transform_gold.py"),
    ("Gold integrity checks and business analytics", "src/run_analytics.py"),
)


def main() -> int:
    missing = [
        relative_path
        for _, relative_path in STAGES
        if not (PROJECT_ROOT / relative_path).is_file()
    ]
    if missing:
        print("Cannot run the pipeline. Missing scripts:", file=sys.stderr)
        for relative_path in missing:
            print(f"  - {relative_path}", file=sys.stderr)
        return 2

    started = perf_counter()
    print("RETAIL DATA PLATFORM — LOCAL PIPELINE", flush=True)
    print("=" * 48, flush=True)

    for number, (name, relative_path) in enumerate(STAGES, start=1):
        print(f"\n[{number}/{len(STAGES)}] {name}", flush=True)
        print("-" * 48, flush=True)
        stage_started = perf_counter()

        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / relative_path)],
            cwd=PROJECT_ROOT,
            check=False,
        )
        elapsed = perf_counter() - stage_started

        if result.returncode != 0:
            print(
                f"\nPIPELINE FAILED at stage {number}: {name} "
                f"(exit code {result.returncode}; {elapsed:.1f}s).",
                file=sys.stderr,
                flush=True,
            )
            return result.returncode if result.returncode > 0 else 1

        print(f"\nStage completed in {elapsed:.1f}s.", flush=True)

    print("\n" + "=" * 48, flush=True)
    print(f"PIPELINE COMPLETED SUCCESSFULLY in {perf_counter() - started:.1f}s.", flush=True)
    print("Report: reports/data_quality/data_quality_report.csv", flush=True)
    print("Quality warnings are reported but do not fail the pipeline.", flush=True)
    print("Gold integrity checks must all report zero issues.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
