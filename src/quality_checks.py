"""Reusable quality checks for five processed Olist Parquet datasets."""
from pathlib import Path
from datetime import datetime, timezone
import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FILES = {
    "orders": "orders.parquet",
    "order_items": "order_items.parquet",
    "products": "products.parquet",
    "customers": "customers.parquet",
    "category_translation": "product_category_name_translation.parquet",
}
EXPECTED_COLUMNS = {
    "orders": {"order_id", "customer_id", "order_status", "order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date"},
    "order_items": {"order_id", "order_item_id", "product_id", "seller_id", "shipping_limit_date", "price", "freight_value"},
    "products": {"product_id", "product_category_name", "product_name_lenght", "product_description_lenght", "product_photos_qty", "product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm"},
    "customers": {"customer_id", "customer_unique_id", "customer_zip_code_prefix", "customer_city", "customer_state"},
    "category_translation": {"product_category_name", "product_category_name_english"},
}

RULES = [('DQ-001', 'Null order IDs', 'orders', 'ERROR', 'SELECT COUNT(*) FROM orders WHERE order_id IS NULL'), ('DQ-002', 'Duplicate order IDs', 'orders', 'ERROR', 'SELECT COUNT(*) FROM (SELECT order_id FROM orders GROUP BY order_id HAVING COUNT(*) > 1)'), ('DQ-003', 'Null customer IDs in orders', 'orders', 'ERROR', 'SELECT COUNT(*) FROM orders WHERE customer_id IS NULL'), ('DQ-004', 'Invalid order statuses', 'orders', 'ERROR', "SELECT COUNT(*) FROM orders WHERE order_status IS NULL OR LOWER(TRIM(order_status)) NOT IN ('approved','invoiced','processing','shipped','delivered','unavailable','canceled','created')"), ('DQ-005', 'Approval before purchase', 'orders', 'ERROR', 'SELECT COUNT(*) FROM orders WHERE order_approved_at < order_purchase_timestamp'), ('DQ-006', 'Delivered orders missing delivery timestamp', 'orders', 'WARNING', "SELECT COUNT(*) FROM orders WHERE LOWER(TRIM(order_status)) = 'delivered' AND order_delivered_customer_date IS NULL"), ('DQ-007', 'Carrier timestamp before approval', 'orders', 'WARNING', 'SELECT COUNT(*) FROM orders WHERE order_delivered_carrier_date < order_approved_at'), ('DQ-008', 'Customer delivery before carrier timestamp', 'orders', 'WARNING', 'SELECT COUNT(*) FROM orders WHERE order_delivered_customer_date < order_delivered_carrier_date'), ('DQ-009', 'Orders with unknown customer', 'orders', 'ERROR', 'SELECT COUNT(*) FROM orders o LEFT JOIN customers c ON o.customer_id = c.customer_id WHERE o.customer_id IS NOT NULL AND c.customer_id IS NULL'), ('DQ-010', 'Null order or item IDs', 'order_items', 'ERROR', 'SELECT COUNT(*) FROM order_items WHERE order_id IS NULL OR order_item_id IS NULL'), ('DQ-011', 'Duplicate order-item keys', 'order_items', 'ERROR', 'SELECT COUNT(*) FROM (SELECT order_id, order_item_id FROM order_items GROUP BY order_id, order_item_id HAVING COUNT(*) > 1)'), ('DQ-012', 'Order items with unknown order', 'order_items', 'ERROR', 'SELECT COUNT(*) FROM order_items i LEFT JOIN orders o ON i.order_id = o.order_id WHERE i.order_id IS NOT NULL AND o.order_id IS NULL'), ('DQ-013', 'Order items with missing or unknown product', 'order_items', 'ERROR', 'SELECT COUNT(*) FROM order_items i LEFT JOIN products p ON i.product_id = p.product_id WHERE i.product_id IS NULL OR p.product_id IS NULL'), ('DQ-014', 'Negative item prices', 'order_items', 'ERROR', 'SELECT COUNT(*) FROM order_items WHERE price < 0'), ('DQ-015', 'Negative freight values', 'order_items', 'ERROR', 'SELECT COUNT(*) FROM order_items WHERE freight_value < 0'), ('DQ-016', 'Null item price or freight', 'order_items', 'ERROR', 'SELECT COUNT(*) FROM order_items WHERE price IS NULL OR freight_value IS NULL'), ('DQ-017', 'Null product IDs', 'products', 'ERROR', 'SELECT COUNT(*) FROM products WHERE product_id IS NULL'), ('DQ-018', 'Duplicate product IDs', 'products', 'ERROR', 'SELECT COUNT(*) FROM (SELECT product_id FROM products GROUP BY product_id HAVING COUNT(*) > 1)'), ('DQ-019', 'Products without category', 'products', 'WARNING', "SELECT COUNT(*) FROM products WHERE product_category_name IS NULL OR TRIM(product_category_name) = ''"), ('DQ-020', 'Negative product weight or dimensions', 'products', 'ERROR', 'SELECT COUNT(*) FROM products WHERE product_weight_g < 0 OR product_length_cm < 0 OR product_height_cm < 0 OR product_width_cm < 0'), ('DQ-021', 'Negative product text lengths or photo count', 'products', 'ERROR', 'SELECT COUNT(*) FROM products WHERE product_name_lenght < 0 OR product_description_lenght < 0 OR product_photos_qty < 0'), ('DQ-022', 'Product categories without translation', 'products', 'WARNING', 'SELECT COUNT(*) FROM (SELECT DISTINCT p.product_category_name FROM products p LEFT JOIN category_translation t ON p.product_category_name = t.product_category_name WHERE p.product_category_name IS NOT NULL AND t.product_category_name IS NULL)'), ('DQ-023', 'Null customer IDs', 'customers', 'ERROR', 'SELECT COUNT(*) FROM customers WHERE customer_id IS NULL'), ('DQ-024', 'Duplicate customer IDs', 'customers', 'ERROR', 'SELECT COUNT(*) FROM (SELECT customer_id FROM customers GROUP BY customer_id HAVING COUNT(*) > 1)'), ('DQ-025', 'Null customer unique IDs', 'customers', 'ERROR', 'SELECT COUNT(*) FROM customers WHERE customer_unique_id IS NULL'), ('DQ-026', 'Customers with missing city or state', 'customers', 'WARNING', "SELECT COUNT(*) FROM customers WHERE customer_city IS NULL OR TRIM(customer_city) = '' OR customer_state IS NULL OR TRIM(customer_state) = ''"), ('DQ-027', 'Invalid state code length', 'customers', 'WARNING', 'SELECT COUNT(*) FROM customers WHERE customer_state IS NOT NULL AND LENGTH(TRIM(customer_state)) <> 2'), ('DQ-028', 'Null source categories in translation', 'category_translation', 'ERROR', 'SELECT COUNT(*) FROM category_translation WHERE product_category_name IS NULL'), ('DQ-029', 'Duplicate source categories in translation', 'category_translation', 'ERROR', 'SELECT COUNT(*) FROM (SELECT product_category_name FROM category_translation GROUP BY product_category_name HAVING COUNT(*) > 1)'), ('DQ-030', 'Missing English translation', 'category_translation', 'ERROR', "SELECT COUNT(*) FROM category_translation WHERE product_category_name_english IS NULL OR TRIM(product_category_name_english) = ''"), ('DQ-031', 'Unused translation categories', 'category_translation', 'WARNING', 'SELECT COUNT(*) FROM (SELECT DISTINCT t.product_category_name FROM category_translation t LEFT JOIN products p ON t.product_category_name = p.product_category_name WHERE p.product_category_name IS NULL)')]


def connect():
    """Create read-only views over existing Parquet files."""
    paths = {name: ROOT / "data" / "processed" / filename for name, filename in FILES.items()}
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing processed Parquet files:\n" + "\n".join(missing))
    con = duckdb.connect(database=":memory:")
    try:
        for name, path in paths.items():
            safe = str(path).replace("'", "''")
            con.execute(f"CREATE VIEW {name} AS SELECT * FROM read_parquet('{safe}')")
        return con
    except Exception:
        con.close()
        raise


def check_schema(con):
    errors = []
    for name, expected in EXPECTED_COLUMNS.items():
        actual = {row[0] for row in con.execute(f"DESCRIBE SELECT * FROM {name}").fetchall()}
        if expected - actual:
            errors.append(f"{name}: missing {', '.join(sorted(expected - actual))}")
    if errors:
        raise ValueError("Processed schema differs from expected Olist columns:\n" + "\n".join(errors))


def run_checks(con):
    check_schema(con)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = []
    for rule_id, name, dataset, severity, query in RULES:
        count = int(con.execute(query).fetchone()[0])
        status = "PASS" if count == 0 else ("FAIL" if severity == "ERROR" else "WARNING")
        rows.append({"rule_id": rule_id, "dataset": dataset, "check_name": name,
                     "severity": severity, "problem_count": count, "status": status,
                     "execution_date": timestamp})
    return pd.DataFrame(rows)


def summarize(results):
    failures = int((results.status == "FAIL").sum())
    warnings = int((results.status == "WARNING").sum())
    overall = "FAILED" if failures else "PASSED_WITH_WARNINGS" if warnings else "PASSED"
    print(results[["rule_id", "dataset", "severity", "problem_count", "status"]].to_string(index=False))
    print(f"\nOverall: {overall} | PASS: {len(results)-failures-warnings} | WARNING: {warnings} | FAIL: {failures}")
    return failures


def save_report(results):
    directory = ROOT / "reports" / "data_quality"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "data_quality_report.csv"
    results.to_csv(path, index=False)
    return path
