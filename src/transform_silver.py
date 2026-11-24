"""Transform the five raw Olist CSV files into typed Silver Parquet files.

Run from the project root:
    python src/transform_orders.py

The input CSV files are never modified. Existing final Parquet files are
replaced only after all five transformations complete successfully.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = PROJECT_ROOT / "data" / "raw"
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"

TRANSFORMATIONS = {
    "orders": (
        "olist_orders_dataset.csv",
        """
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
    ),
    "order_items": (
        "olist_order_items_dataset.csv",
        """
            NULLIF(TRIM(order_id), '') AS order_id,
            TRY_CAST(order_item_id AS INTEGER) AS order_item_id,
            NULLIF(TRIM(product_id), '') AS product_id,
            NULLIF(TRIM(seller_id), '') AS seller_id,
            TRY_CAST(shipping_limit_date AS TIMESTAMP)
                AS shipping_limit_date,
            TRY_CAST(price AS DOUBLE) AS price,
            TRY_CAST(freight_value AS DOUBLE) AS freight_value
        """,
    ),
    "products": (
        "olist_products_dataset.csv",
        """
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
    ),
    "customers": (
        "olist_customers_dataset.csv",
        """
            NULLIF(TRIM(customer_id), '') AS customer_id,
            NULLIF(TRIM(customer_unique_id), '') AS customer_unique_id,
            NULLIF(TRIM(customer_zip_code_prefix), '')
                AS customer_zip_code_prefix,
            NULLIF(TRIM(customer_city), '') AS customer_city,
            NULLIF(TRIM(customer_state), '') AS customer_state
        """,
    ),
    "product_category_name_translation": (
        "product_category_name_translation.csv",
        """
            NULLIF(TRIM(product_category_name), '') AS product_category_name,
            NULLIF(TRIM(product_category_name_english), '')
                AS product_category_name_english
        """,
    ),
}


def sql_path(path: Path) -> str:
    """Escape a filesystem path for use inside a single-quoted SQL string."""
    return str(path.resolve()).replace("'", "''")


def main() -> None:
    missing_sources = [
        str(RAW_PATH / filename)
        for filename, _ in TRANSFORMATIONS.values()
        if not (RAW_PATH / filename).is_file()
    ]
    if missing_sources:
        raise FileNotFoundError(
            "Missing raw CSV files:\n" + "\n".join(missing_sources)
        )

    PROCESSED_PATH.mkdir(parents=True, exist_ok=True)
    row_counts = {}
    con = duckdb.connect(database=":memory:")

    try:
        # Build every file before replacing existing processed outputs.
        with TemporaryDirectory(prefix="silver_build_", dir=PROCESSED_PATH) as temp_dir:
            temp_path = Path(temp_dir)
            for table_name, (source_name, select_columns) in TRANSFORMATIONS.items():
                source_file = RAW_PATH / source_name
                temporary_output = temp_path / f"{table_name}.parquet"

                con.execute(
                    f"""
                    COPY (
                        SELECT {select_columns}
                        FROM read_csv_auto(
                            '{sql_path(source_file)}',
                            all_varchar = true
                        )
                    )
                    TO '{sql_path(temporary_output)}'
                    (FORMAT PARQUET)
                    """
                )
                row_counts[table_name] = con.execute(
                    f"SELECT COUNT(*) FROM read_parquet('{sql_path(temporary_output)}')"
                ).fetchone()[0]

            for table_name in TRANSFORMATIONS:
                (temp_path / f"{table_name}.parquet").replace(
                    PROCESSED_PATH / f"{table_name}.parquet"
                )
    finally:
        con.close()

    print("Silver transformations completed successfully!\n")
    for table_name, total_rows in row_counts.items():
        print(f"{table_name}.parquet: {total_rows:,} rows")
    print(f"\nOutput folder: {PROCESSED_PATH}")


if __name__ == "__main__":
    main()
