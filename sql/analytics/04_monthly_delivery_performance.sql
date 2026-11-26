-- Delivery performance for orders marked delivered.
-- 'Late' means the calendar date of delivery exceeds the estimated delivery date.
-- Orders with a missing actual/estimated date are excluded from the late % denominator.
SELECT
    CAST(DATE_TRUNC('month', order_purchase_date) AS DATE) AS purchase_month,
    COUNT(*) AS delivered_orders,
    COUNT(*) FILTER (
        WHERE order_delivered_customer_date IS NOT NULL
          AND order_estimated_delivery_date IS NOT NULL
    ) AS orders_with_comparable_dates,
    COUNT(*) FILTER (
        WHERE order_delivered_customer_date IS NOT NULL
          AND order_estimated_delivery_date IS NOT NULL
          AND CAST(order_delivered_customer_date AS DATE)
              > CAST(order_estimated_delivery_date AS DATE)
    ) AS late_deliveries,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE order_delivered_customer_date IS NOT NULL
              AND order_estimated_delivery_date IS NOT NULL
              AND CAST(order_delivered_customer_date AS DATE)
                  > CAST(order_estimated_delivery_date AS DATE)
        ) / NULLIF(
            COUNT(*) FILTER (
                WHERE order_delivered_customer_date IS NOT NULL
                  AND order_estimated_delivery_date IS NOT NULL
            ), 0
        ), 2
    ) AS late_delivery_pct,
    ROUND(AVG(delivery_lead_days), 1) AS average_delivery_lead_days
FROM read_parquet('data/gold/fact_orders.parquet')
WHERE order_status = 'delivered'
GROUP BY 1
ORDER BY purchase_month;
