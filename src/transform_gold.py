"""Build analytical Gold Parquet models from the five validated Silver datasets.

Run from the repository root:
    python src/transform_gold.py

Inputs: data/processed/*.parquet (Silver)
Outputs: data/gold/{fact_orders,fact_order_items,dim_products,dim_customers}.parquet

No source, Bronze, or Silver file is modified. All four Gold files are built
and checked before they are promoted into the final directory.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SILVER_DIR = PROJECT_ROOT / "data" / "processed"
GOLD_DIR = PROJECT_ROOT / "data" / "gold"

INPUTS = {
    "orders": "orders.parquet",
    "order_items": "order_items.parquet",
    "products": "products.parquet",
    "customers": "customers.parquet",
    "category_translation": "product_category_name_translation.parquet",
}

# Each model has a clearly defined grain:
#   fact_orders: one row per order
#   fact_order_items: one row per (order_id, order_item_id)
#   dim_products: one row per product
#   dim_customers: one row per customer record
MODELS = {
    "dim_products": """
        SELECT
            p.product_id,
            p.product_category_name AS category_name_original,
            t.product_category_name_english AS category_name_english,
            COALESCE(
                NULLIF(TRIM(t.product_category_name_english), ''),
                NULLIF(TRIM(p.product_category_name), ''),
                'unclassified'
            ) AS category_label,
            p.product_name_lenght AS product_name_length,
            p.product_description_lenght AS product_description_length,
            p.product_photos_qty,
            p.product_weight_g,
            p.product_length_cm,
            p.product_height_cm,
            p.product_width_cm
        FROM products AS p
        LEFT JOIN category_translation AS t
            ON p.product_category_name = t.product_category_name
    """,
    "dim_customers": """
        SELECT
            customer_id,
            customer_unique_id,
            customer_zip_code_prefix,
            customer_city,
            customer_state
        FROM customers
    """,
    "fact_order_items": """
        SELECT
            i.order_id,
            i.order_item_id,
            o.customer_id,
            i.product_id,
            i.seller_id,
            o.order_status,
            o.order_purchase_timestamp,
            CAST(o.order_purchase_timestamp AS DATE) AS order_purchase_date,
            i.shipping_limit_date,
            i.price AS item_price,
            i.freight_value,
            (i.price + i.freight_value) AS line_total_amount
        FROM order_items AS i
        INNER JOIN orders AS o
            ON i.order_id = o.order_id
    """,
    "fact_orders": """
        SELECT
            o.order_id,
            o.customer_id,
            o.order_status,
            o.order_purchase_timestamp,
            CAST(o.order_purchase_timestamp AS DATE) AS order_purchase_date,
            o.order_approved_at,
            o.order_delivered_carrier_date,
            o.order_delivered_customer_date,
            o.order_estimated_delivery_date,
            COALESCE(i.order_item_count, 0) AS order_item_count,
            COALESCE(i.item_value, 0) AS item_value,
            COALESCE(i.freight_value, 0) AS freight_value,
            COALESCE(i.order_total_amount, 0) AS order_total_amount,
            CASE
                WHEN o.order_status = 'delivered'
                 AND o.order_purchase_timestamp IS NOT NULL
                 AND o.order_delivered_customer_date IS NOT NULL
                THEN DATE_DIFF(
                    'day',
                    CAST(o.order_purchase_timestamp AS DATE),
                    CAST(o.order_delivered_customer_date AS DATE)
                )
                ELSE NULL
            END AS delivery_lead_days,
            CASE
                WHEN o.order_status = 'delivered'
                 AND o.order_delivered_customer_date IS NOT NULL
                 AND o.order_estimated_delivery_date IS NOT NULL
                THEN CAST(o.order_delivered_customer_date AS DATE)
                     > CAST(o.order_estimated_delivery_date AS DATE)
                ELSE NULL
            END AS delivered_late
        FROM orders AS o
        LEFT JOIN (
            SELECT
                order_id,
                COUNT(*) AS order_item_count,
                SUM(price) AS item_value,
                SUM(freight_value) AS freight_value,
                SUM(price + freight_value) AS order_total_amount
            FROM order_items
            GROUP BY order_id
        ) AS i ON o.order_id = i.order_id
    """,
}


def sql_path(path: Path) -> str:
    """Escape an absolute path for use as a single-quoted SQL string."""
    return str(path.resolve()).replace("'", "''")


def row_count(connection: duckdb.DuckDBPyConnection, view_name: str) -> int:
    return int(connection.execute(f"SELECT COUNT(*) FROM {view_name}").fetchone()[0])


def check_unique_key(
    connection: duckdb.DuckDBPyConnection, view_name: str, key_columns: str
) -> None:
    duplicates = connection.execute(
        f"""
        SELECT COUNT(*) FROM (
            SELECT {key_columns}
            FROM {view_name}
            GROUP BY {key_columns}
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]
    if duplicates:
        raise ValueError(
            f"Gold model {view_name} contains {duplicates} duplicate key groups"
        )


def main() -> None:
    missing = [
        SILVER_DIR / filename
        for filename in INPUTS.values()
        if not (SILVER_DIR / filename).is_file()
    ]
    if missing:
        raise FileNotFoundError(
            "Missing Silver Parquet files:\n"
            + "\n".join(f"- {path}" for path in missing)
            + "\nRun python src/run_pipeline.py first."
        )

    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(database=":memory:")
    counts = {}

    try:
        for view_name, filename in INPUTS.items():
            connection.execute(
                f"CREATE VIEW {view_name} AS "
                f"SELECT * FROM read_parquet('{sql_path(SILVER_DIR / filename)}')"
            )

        for model_name, query in MODELS.items():
            connection.execute(f"CREATE VIEW {model_name} AS {query}")

        expected_counts = {
            "dim_products": row_count(connection, "products"),
            "dim_customers": row_count(connection, "customers"),
            "fact_order_items": row_count(connection, "order_items"),
            "fact_orders": row_count(connection, "orders"),
        }

        # Check Gold's grain and detect row multiplication or row loss in joins.
        for model_name, expected in expected_counts.items():
            actual = row_count(connection, model_name)
            if actual != expected:
                raise ValueError(
                    f"Row-count mismatch in {model_name}: "
                    f"expected {expected:,}, got {actual:,}"
                )
            counts[model_name] = actual

        check_unique_key(connection, "dim_products", "product_id")
        check_unique_key(connection, "dim_customers", "customer_id")
        check_unique_key(connection, "fact_order_items", "order_id, order_item_id")
        check_unique_key(connection, "fact_orders", "order_id")

        with TemporaryDirectory(prefix="gold_build_", dir=GOLD_DIR) as temporary:
            temporary_dir = Path(temporary)
            for model_name in MODELS:
                output_file = temporary_dir / f"{model_name}.parquet"
                connection.execute(
                    f"COPY (SELECT * FROM {model_name}) "
                    f"TO '{sql_path(output_file)}' (FORMAT PARQUET)"
                )
                if connection.execute(
                    "SELECT COUNT(*) FROM read_parquet(?)", [str(output_file)]
                ).fetchone()[0] != counts[model_name]:
                    raise ValueError(f"Written Parquet count mismatch: {model_name}")

            # Replacement across multiple files is not a single atomic transaction.
            for model_name in MODELS:
                (temporary_dir / f"{model_name}.parquet").replace(
                    GOLD_DIR / f"{model_name}.parquet"
                )
    finally:
        connection.close()

    print("Gold models generated successfully!\n")
    for model_name, count in counts.items():
        print(f"{model_name}.parquet: {count:,} rows (grain verified)")
    print(f"\nOutput folder: {GOLD_DIR}")
    print("Raw, Bronze, and Silver files were not changed.")


if __name__ == "__main__":
    main()
