-- Monthly value of items plus freight for delivered orders with item data.
-- This is NOT recognized revenue: payments, refunds and returns are not modeled.
SELECT
    CAST(DATE_TRUNC('month', order_purchase_date) AS DATE) AS purchase_month,
    COUNT(*) AS delivered_orders_with_items,
    ROUND(SUM(order_total_amount), 2) AS recorded_order_value_brl,
    ROUND(AVG(order_total_amount), 2) AS average_order_value_brl,
    ROUND(SUM(freight_value), 2) AS recorded_freight_brl
FROM read_parquet('data/gold/fact_orders.parquet')
WHERE order_status = 'delivered'
  AND order_total_amount IS NOT NULL
GROUP BY 1
ORDER BY purchase_month;
