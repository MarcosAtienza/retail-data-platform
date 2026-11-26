-- Overall order status profile across every order.
-- An order with no item rows has an aggregated amount of zero in fact_orders.
-- Therefore use order_item_count, not order_total_amount IS NULL, to detect it.
-- Recorded amounts are item + freight values, not recognized revenue.
SELECT
    order_status,
    COUNT(*) AS orders,
    COUNT(*) FILTER (WHERE order_item_count > 0) AS orders_with_items,
    COUNT(*) FILTER (WHERE order_item_count = 0) AS orders_without_items,
    ROUND(SUM(COALESCE(order_total_amount, 0)), 2) AS recorded_order_value_brl
FROM read_parquet('data/gold/fact_orders.parquet')
GROUP BY order_status
ORDER BY orders DESC, order_status;
