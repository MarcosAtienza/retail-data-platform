"""Transform the five Olist Bronze Parquet datasets into typed Silver Parquet.

Run from the project root:
    python src/transform_silver.py

Reads only data/bronze/*.parquet; never modifies Bronze or the raw CSVs.
All five outputs are built and row-count-checked before replacing Silver files.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRONZE_PATH = PROJECT_ROOT / "data" / "bronze"
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"

# Preserve the field names expected by quality_checks.py.
# TRY_CAST keeps unparseable source values as NULL for subsequent quality checks.
TRANSFORMATIONS = {
    "orders": """
        NULLIF(TRIM(order_id), '') AS order_id,
        NULLIF(TRIM(customer_id), '') AS customer_id,
        NULLIF(TRIM(order_status), '') AS order_status,
        TRY_CAST(order_purchase_timestamp AS TIMESTAMP)
            AS order_purchase_timestamp,
        TRY_CAST(order_approved_at AS TIMESTAMP)
            AS order_approved_at,
        TRY_CAST(order_delivered_carrier_date AS TIMESTAMP)
            AS order_delivered_carrier_date,
        TRY_CAST(order_delivered_customer_date AS TIMESTAMP)
            AS order_delivered_customer_date,
        TRY_CAST(order_estimated_delivery_date AS TIMESTAMP)
            AS order_estimated_delivery_date
    """,
    "order_items": """
        NULLIF(TRIM(order_id), '') AS order_id,
        TRY_CAST(order_item_id AS INTEGER) AS order_item_id,
        NULLIF(TRIM(product_id), '') AS product_id,
        NULLIF(TRIM(seller_id), '') AS seller_id,
        TRY_CAST(shipping_limit_date AS TIMESTAMP)
            AS shipping_limit_date,
        TRY_CAST(price AS DOUBLE) AS price,
        TRY_CAST(freight_value AS DOUBLE) AS freight_value
    """,
    "products": """
        NULLIF(TRIM(product_id), '') AS product_id,
        NULLIF(TRIM(product_category_name), '') AS product_category_name,
        TRY_CAST(product_name_lenght AS INTEGER) AS product_name_lenght,
        TRY_CAST(product_description_lenght AS INTEGER)
            AS product_description_lenght,
        TRY_CAST(product_photos_qty AS INTEGER) AS product_photos_qty,
        TRY_CAST(product_weight_g AS DOUBLE) AS product_weight_g,
        TRY_CAST(product_length_cm AS DOUBLE) AS product_length_cm,
        TRY_CAST(product_height_cm AS DOUBLE) AS product_height_cm,
        TRY_CAST(product_width_cm AS DOUBLE) AS product_width_cm
    """,
    "customers": """
        NULLIF(TRIM(customer_id), '') AS customer_id,
        NULLIF(TRIM(customer_unique_id), '') AS customer_unique_id,
        NULLIF(TRIM(customer_zip_code_prefix), '')
            AS customer_zip_code_prefix,
        NULLIF(TRIM(customer_city), '') AS customer_city,
        NULLIF(TRIM(customer_state), '') AS customer_state
    """,
    "product_category_name_translation": """
        NULLIF(TRIM(product_category_name), '') AS product_category_name,
        NULLIF(TRIM(product_category_name_english), '')
            AS product_category_name_english
    """,
}


def sql_path(path: Path) -> str:
    """Escape a filesystem path for use inside a DuckDB SQL string literal."""
    return str(path.resolve()).replace("'", "''")


def main() -> None:
    missing_sources = [
        str(BRONZE_PATH / f"{dataset}.parquet")
        for dataset in TRANSFORMATIONS
        if not (BRONZE_PATH / f"{dataset}.parquet").is_file()
    ]
    if missing_sources:
        raise FileNotFoundError(
            "Missing Bronze Parquet files:\n"
            + "\n".join(f"- {path}" for path in missing_sources)
            + "\nRun python src/ingest_bronze.py first."
        )

    PROCESSED_PATH.mkdir(parents=True, exist_ok=True)
    row_counts = {}
    con = duckdb.connect(database=":memory:")

    try:
        # Build every Silver file before replacing existing outputs.
        with TemporaryDirectory(prefix="silver_build_", dir=PROCESSED_PATH) as tmp:
            temp_path = Path(tmp)
            for dataset, select_columns in TRANSFORMATIONS.items():
                bronze_file = BRONZE_PATH / f"{dataset}.parquet"
                temporary_output = temp_path / f"{dataset}.parquet"

                bronze_rows = con.execute(
                    f"SELECT COUNT(*) FROM read_parquet('{sql_path(bronze_file)}')"
                ).fetchone()[0]

                con.execute(
                    f"""
                    COPY (
                        SELECT {select_columns}
                        FROM read_parquet('{sql_path(bronze_file)}')
                    )
                    TO '{sql_path(temporary_output)}'
                    (FORMAT PARQUET)
                    """
                )

                silver_rows = con.execute(
                    f"SELECT COUNT(*) FROM read_parquet('{sql_path(temporary_output)}')"
                ).fetchone()[0]
                if bronze_rows != silver_rows:
                    raise ValueError(
                        f"Row count mismatch in {dataset}: "
                        f"Bronze={bronze_rows}, Silver={silver_rows}"
                    )
                row_counts[dataset] = silver_rows

            # Replace final files only after every transform and count check passes.
            for dataset in TRANSFORMATIONS:
                (temp_path / f"{dataset}.parquet").replace(
                    PROCESSED_PATH / f"{dataset}.parquet"
                )
    finally:
        con.close()

    print("Silver transformations completed successfully!\n")
    for dataset, total_rows in row_counts.items():
        print(f"{dataset}.parquet: {total_rows:,} rows (Bronze count verified)")
    print(f"\nOutput folder: {PROCESSED_PATH}")
    print("Bronze Parquet files and original CSVs were not changed.")


if __name__ == "__main__":
    main()
