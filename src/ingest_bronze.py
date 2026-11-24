"""Ingest the five original Olist CSVs into the local Bronze layer.

Usage (from the project root):
    python src/ingest_bronze.py

Bronze stores the source columns and values as strings in Parquet, without
business transformations or type casting. The original CSV files are kept.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze"

# Output names match the corresponding Silver table names.
DATASETS = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "products": "olist_products_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "product_category_name_translation": "product_category_name_translation.csv",
}


def sql_path(path: Path) -> str:
    """Escape a path used inside a single-quoted DuckDB SQL string."""
    return str(path.resolve()).replace("'", "''")


def main() -> None:
    missing = [str(RAW_DIR / filename) for filename in DATASETS.values()
               if not (RAW_DIR / filename).is_file()]
    if missing:
        raise FileNotFoundError(
            "Missing original CSV files:\n" + "\n".join(f"- {p}" for p in missing)
        )

    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    counts = {}
    connection = duckdb.connect(database=":memory:")

    try:
        # Build all five outputs first; do not overwrite previous outputs on
        # a failed CSV read or a failed validation.
        with TemporaryDirectory(prefix="bronze_build_", dir=BRONZE_DIR) as tmp:
            temporary_dir = Path(tmp)

            for dataset, csv_name in DATASETS.items():
                csv_file = RAW_DIR / csv_name
                parquet_file = temporary_dir / f"{dataset}.parquet"

                # all_varchar avoids CSV type inference, preserving identifiers
                # such as postal-code prefixes and the original field names.
                csv_source = (
                    f"read_csv_auto('{sql_path(csv_file)}', all_varchar = true)"
                )
                connection.execute(
                    f"COPY (SELECT * FROM {csv_source}) "
                    f"TO '{sql_path(parquet_file)}' (FORMAT PARQUET)"
                )

                source_rows = connection.execute(
                    f"SELECT COUNT(*) FROM {csv_source}"
                ).fetchone()[0]
                bronze_rows = connection.execute(
                    "SELECT COUNT(*) FROM read_parquet(?)", [str(parquet_file)]
                ).fetchone()[0]

                if source_rows != bronze_rows:
                    raise ValueError(
                        f"Row count mismatch for {dataset}: "
                        f"CSV={source_rows}, Bronze={bronze_rows}"
                    )
                counts[dataset] = bronze_rows

            # Promote files only when all five builds and checks succeeded.
            for dataset in DATASETS:
                (temporary_dir / f"{dataset}.parquet").replace(
                    BRONZE_DIR / f"{dataset}.parquet"
                )
    finally:
        connection.close()

    print("Bronze ingestion completed successfully!\n")
    for dataset, rows in counts.items():
        print(f"{dataset}.parquet: {rows:,} rows (CSV count verified)")
    print(f"\nOutput folder: {BRONZE_DIR}")
    print("Original CSV files were not changed.")


if __name__ == "__main__":
    main()
