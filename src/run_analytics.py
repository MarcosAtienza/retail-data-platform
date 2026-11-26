"""Run and validate SQL analyses against the four Gold Parquet datasets.

Usage from any working directory:
    python src/run_analytics.py

All SQL queries are stored under sql/analytics/. The 00_gold_model_checks.sql
query is mandatory and must report no issues; otherwise the command fails.
The script does not modify any dataset or create reports.
"""

from pathlib import Path
import os
import sys

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parent.parent
GOLD_DIR = PROJECT_ROOT / "data" / "gold"
QUERIES_DIR = PROJECT_ROOT / "sql" / "analytics"
REQUIRED_TABLES = (
    "fact_orders.parquet",
    "fact_order_items.parquet",
    "dim_products.parquet",
    "dim_customers.parquet",
)
MODEL_CHECKS_FILENAME = "00_gold_model_checks.sql"


def main() -> int:
    missing = [
        str(GOLD_DIR / filename)
        for filename in REQUIRED_TABLES
        if not (GOLD_DIR / filename).is_file()
    ]
    if missing:
        print("Missing Gold Parquet files:", file=sys.stderr)
        for path in missing:
            print(f"  - {path}", file=sys.stderr)
        print("Run `python src/transform_gold.py` first.", file=sys.stderr)
        return 2

    queries = sorted(QUERIES_DIR.glob("*.sql"))
    if not queries:
        print("No SQL queries found in sql/analytics/.", file=sys.stderr)
        return 2
    if not (QUERIES_DIR / MODEL_CHECKS_FILENAME).is_file():
        print(f"Required SQL checks not found: {MODEL_CHECKS_FILENAME}", file=sys.stderr)
        return 2

    original_cwd = Path.cwd()
    connection = duckdb.connect(database=":memory:")
    try:
        # The standalone SQL files use project-root-relative Parquet paths.
        os.chdir(PROJECT_ROOT)
        print("GOLD ANALYTICS — RETAIL DATA PLATFORM", flush=True)
        print("=" * 58, flush=True)

        for query_path in queries:
            print(f"\n{query_path.name}", flush=True)
            print("-" * 58, flush=True)
            query = query_path.read_text(encoding="utf-8")
            try:
                result = connection.execute(query).fetchdf()
            except Exception as exc:
                print(f"SQL query failed: {query_path.name}", file=sys.stderr)
                print(str(exc), file=sys.stderr)
                return 1

            print(
                result.to_string(index=False) if not result.empty else "(no rows)",
                flush=True,
            )

            if query_path.name == MODEL_CHECKS_FILENAME:
                required_columns = {"check_name", "issue_count"}
                if result.empty or not required_columns.issubset(result.columns):
                    print("Invalid or empty Gold integrity-check results.", file=sys.stderr)
                    return 1
                if result["check_name"].isna().any() or result["check_name"].duplicated().any():
                    print("Invalid duplicate or null check names in integrity results.", file=sys.stderr)
                    return 1
                failures = result[
                    result["issue_count"].isna() | (result["issue_count"] != 0)
                ]
                if not failures.empty:
                    print(
                        f"Gold integrity checks FAILED: {len(failures)} check(s) "
                        "with nonzero/missing issue counts.",
                        file=sys.stderr,
                    )
                    return 1
                print(f"Gold integrity checks passed: {len(result)} checks.", flush=True)

        print("\nAll Gold SQL queries executed successfully.", flush=True)
        return 0
    finally:
        connection.close()
        os.chdir(original_cwd)


if __name__ == "__main__":
    raise SystemExit(main())
