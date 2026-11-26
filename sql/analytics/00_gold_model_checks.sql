-- Gold model consistency checks. Each row represents one potential issue.
-- A nonzero value requires investigation before relying on business metrics.
WITH
orders AS (
    SELECT * FROM read_parquet('data/gold/fact_orders.parquet')
),
items AS (
    SELECT * FROM read_parquet('data/gold/fact_order_items.parquet')
),
products AS (
    SELECT * FROM read_parquet('data/gold/dim_products.parquet')
),
customers AS (
    SELECT * FROM read_parquet('data/gold/dim_customers.parquet')
),
checks AS (
    SELECT 'duplicate_order_keys' AS check_name, COUNT(*) AS issue_count
    FROM (
        SELECT order_id FROM orders GROUP BY order_id HAVING COUNT(*) > 1
    )

    UNION ALL
    SELECT 'duplicate_order_item_keys', COUNT(*)
    FROM (
        SELECT order_id, order_item_id
        FROM items
        GROUP BY order_id, order_item_id
        HAVING COUNT(*) > 1
    )

    UNION ALL
    SELECT 'duplicate_product_keys', COUNT(*)
    FROM (
        SELECT product_id FROM products GROUP BY product_id HAVING COUNT(*) > 1
    )

    UNION ALL
    SELECT 'duplicate_customer_keys', COUNT(*)
    FROM (
        SELECT customer_id FROM customers GROUP BY customer_id HAVING COUNT(*) > 1
    )

    UNION ALL
    SELECT 'orders_without_matching_customer', COUNT(*)
    FROM orders o
    LEFT JOIN customers c ON o.customer_id = c.customer_id
    WHERE c.customer_id IS NULL

    UNION ALL
    SELECT 'items_without_matching_order', COUNT(*)
    FROM items i
    LEFT JOIN orders o ON i.order_id = o.order_id
    WHERE o.order_id IS NULL

    UNION ALL
    SELECT 'items_without_matching_product', COUNT(*)
    FROM items i
    LEFT JOIN products p ON i.product_id = p.product_id
    WHERE p.product_id IS NULL

    UNION ALL
    SELECT 'order_amount_mismatches_gt_0_01', COUNT(*)
    FROM orders o
    JOIN (
        SELECT order_id, SUM(line_total_amount) AS total_from_items
        FROM items GROUP BY order_id
    ) i ON o.order_id = i.order_id
    WHERE o.order_total_amount IS NULL
       OR ABS(o.order_total_amount - i.total_from_items) > 0.01
)
SELECT check_name, issue_count
FROM checks
ORDER BY check_name;
