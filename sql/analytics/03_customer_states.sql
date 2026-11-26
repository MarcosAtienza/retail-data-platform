-- Distribution of delivered orders by customer state (not seller state).
SELECT
    COALESCE(NULLIF(TRIM(c.customer_state), ''), 'Unknown') AS customer_state,
    COUNT(*) AS delivered_orders,
    ROUND(SUM(o.order_total_amount), 2) AS recorded_order_value_brl,
    ROUND(AVG(o.order_total_amount), 2) AS average_order_value_brl
FROM read_parquet('data/gold/fact_orders.parquet') o
LEFT JOIN read_parquet('data/gold/dim_customers.parquet') c
    ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered'
  AND o.order_total_amount IS NOT NULL
GROUP BY 1
ORDER BY delivered_orders DESC, customer_state
LIMIT 15;
