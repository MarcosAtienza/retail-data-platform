from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"

orders_file = PROCESSED_PATH / "orders.parquet"
order_items_file = PROCESSED_PATH / "order_items.parquet"

con = duckdb.connect()

print("Starting data quality checks...")

result = con.execute(f"""
    SELECT
        COUNT(*) AS null_order_ids
    FROM read_parquet('{orders_file}')
    WHERE order_id IS NULL
""").fetchdf()

print("\n1. Null order IDs:")
print(result)

result = con.execute(f"""
    SELECT
        order_id,
        COUNT(*) AS occurrences
    FROM read_parquet('{orders_file}')
    GROUP BY order_id
    HAVING COUNT(*) > 1
""").fetchdf()

print("\n2. Duplicated order IDs:")
print(result)

result = con.execute(f"""
    SELECT
    order_id,
    order_item_id,
    COUNT (*) AS occurrences
    FROM read_parquet('{order_items_file}')
    GROUP BY order_id, order_item_id
    HAVING COUNT(*) > 1
""").fetchdf()

print("\n3. Duplicated order item composed IDs:")
print(result)

result = con.execute(f"""
    SELECT
        COUNT(*) AS orphan_order_items
    FROM read_parquet('{order_items_file}') AS oi
    LEFT JOIN read_parquet('{orders_file}') AS o
        ON o.order_id = oi.order_id
    WHERE o.order_id IS NULL
""").fetchdf()

print("\n4. Orphan order items:")
print(result)

result = con.execute(f"""
    SELECT
        COUNT(*) AS negative_price_values
    FROM read_parquet('{order_items_file}')
    WHERE price < 0
""").fetchdf()

print("\n5. Negative prices:")
print(result)

result = con.execute(f"""
    SELECT
        COUNT(*) AS null_prices
    FROM read_parquet('{order_items_file}')
    WHERE price IS NULL
""").fetchdf()

print("\n6. Null prices:")
print(result)

result = con.execute(f"""
    SELECT
        COUNT(*) AS negative_fright_values
    FROM read_parquet('{order_items_file}')
    WHERE freight_value < 0
""").fetchdf()

print("\n7. Negative freight values:")
print(result)

result = con.execute(f"""
    SELECT
        COUNT(*) AS null_freight_values
    FROM read_parquet('{order_items_file}')
    WHERE freight_value IS NULL
""").fetchdf()

print("\n8. Null freight values:")
print(result)

result = con.execute(f"""
    DESCRIBE
    SELECT *
    FROM read_parquet('{orders_file}')
""").fetchdf()

print("\n9. Orders column types:")
print(result)

result = con.execute(f"""
    SELECT
        order_status,
        COUNT(*) AS total_orders,
        COUNT(*) FILTER (WHERE order_approved_at IS NULL) AS null_approved_dates,
        COUNT(*) FILTER (WHERE order_delivered_carrier_date IS NULL) AS null_carrier_dates,
        COUNT(*) FILTER (WHERE order_delivered_customer_date IS NULL) AS null_customer_delivery_dates
    FROM read_parquet('{orders_file}')
    GROUP BY order_status
    ORDER BY total_orders DESC
""").fetchdf()

print("\n10. Null dates by order status:")
print(result)

result = con.execute(f"""
    SELECT COUNT(*) AS invalid_delivery_dates
    FROM read_parquet('{orders_file}')
    WHERE order_purchase_timestamp
          > order_approved_at
          OR
          order_approved_at
          > order_delivered_carrier_date
          OR
          order_delivered_carrier_date
          > order_delivered_customer_date
""").fetchdf()

print("\n11. Invalid delivery dates:")
print(result)
