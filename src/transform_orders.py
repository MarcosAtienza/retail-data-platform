from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = PROJECT_ROOT / "data" / "raw"
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"

PROCESSED_PATH.mkdir(parents=True, exist_ok=True)

orders_file = RAW_PATH / "olist_orders_dataset.csv"
order_items_file = RAW_PATH / "olist_order_items_dataset.csv"

orders_output = PROCESSED_PATH / "orders.parquet"
order_items_output = PROCESSED_PATH / "order_items.parquet"

con = duckdb.connect()

con.execute(f"""
    COPY (
        SELECT
            TRIM(order_id) AS order_id,
            TRIM(customer_id) AS customer_id,
            TRIM(order_status) AS order_status,
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
        FROM read_csv_auto('{orders_file}')
    )
    TO '{orders_output}'
    (FORMAT PARQUET)
""")

con.execute(f"""
    COPY (
        SELECT
            TRIM(order_id) AS order_id,
            TRY_CAST(order_item_id AS INTEGER) AS order_item_id,
            TRIM(product_id) AS product_id,
            TRIM(seller_id) AS seller_id,
            TRY_CAST(shipping_limit_date AS TIMESTAMP)
                AS shipping_limit_date,
            TRY_CAST(price AS DOUBLE) AS price,
            TRY_CAST(freight_value AS DOUBLE) AS freight_value
        FROM read_csv_auto('{order_items_file}')
    )
    TO '{order_items_output}'
    (FORMAT PARQUET)
""")

print("Transformations completed!")

for table in ["orders", "order_items"]:
    output_file = PROCESSED_PATH / f"{table}.parquet"

    result = con.execute(f"""
        SELECT COUNT(*) AS total_rows
        FROM read_parquet('{output_file}')
    """).fetchdf()

    print(f"\n{table}:")
    print(result)

con.close()