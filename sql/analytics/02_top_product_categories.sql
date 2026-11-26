-- Top categories for delivered order items, ranked by item price (excl. freight).
-- distinct_orders is not additive across categories: an order may span categories.
SELECT
    COALESCE(NULLIF(TRIM(p.category_label), ''), 'Uncategorized') AS category,
    COUNT(*) AS item_rows,
    COUNT(DISTINCT i.order_id) AS distinct_orders,
    ROUND(SUM(i.item_price), 2) AS item_value_brl,
    ROUND(SUM(i.freight_value), 2) AS freight_value_brl,
    ROUND(SUM(i.line_total_amount), 2) AS total_including_freight_brl
FROM read_parquet('data/gold/fact_order_items.parquet') i
LEFT JOIN read_parquet('data/gold/dim_products.parquet') p
    ON i.product_id = p.product_id
WHERE i.order_status = 'delivered'
GROUP BY 1
ORDER BY item_value_brl DESC, category
LIMIT 15;
