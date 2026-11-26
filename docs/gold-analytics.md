# Gold Analytics — Retail Data Platform

## Scope

Five business analyses and one additional consistency check run against four local Gold Parquet tables: `fact_orders`, `fact_order_items`, `dim_products`, and `dim_customers`.

Run from the project root (or any working directory):

```bash
python src/run_analytics.py
```

This runs every SQL file in `sql/analytics/` in filename order. It reads Gold data without changing it.
The first file, `00_gold_model_checks.sql`, is mandatory. If any of its issue counts is nonzero (or missing), the runner exits with a failure code and does not continue to business queries. The SQL files use paths relative to the project root; `run_analytics.py` ensures that working directory automatically.

## SQL inventory

| File | Purpose | Grain / denominator |
|---|---|---|
| `00_gold_model_checks.sql` | Duplicate keys, missing parent records, order amount reconciliation | Counts potential issues; ideally all zero |
| `01_monthly_order_value.sql` | Monthly recorded order value and average order value | Delivered orders with an item amount; grouped by purchase month |
| `02_top_product_categories.sql` | Top 15 product categories by item price | Delivered order-item rows; distinct orders are not additive across categories |
| `03_customer_states.sql` | Top customer states | Delivered orders with an item amount, grouped by customer state |
| `04_monthly_delivery_performance.sql` | Monthly deliveries and lateness | Delivered orders; lateness denominator includes only comparable actual and estimated delivery dates |
| `05_order_status_overview.sql` | Distribution of order statuses and counts with/without item rows | All orders, including canceled and unavailable |

## Important interpretation rules

1. **Recorded order value is not recognized revenue.** The files do not model payment confirmation, refunds, returns, taxes, or accounting recognition. Treat `order_total_amount` as a sum of recorded item prices plus freight.
2. **Different grains must not be mixed.** `fact_orders` has one row per order. `fact_order_items` has one row per ordered item. Joining them and then summing order-level metrics would duplicate those values for multi-item orders.
3. **Order status matters.** The sales-oriented analyses focus on delivered orders, but even a delivered status does not by itself prove a completed payment.
4. **Lateness is measured by dates, not timestamps.** The delivery query compares the actual delivery calendar day against the estimated delivery day, and excludes missing dates from the lateness percentage denominator.
5. **Customer state is not seller state.** Geographic analyses use the location tied to the customer record.
6. **Category orders are not additive.** The same order can contain items from several categories.
7. **Source anomalies remain visible.** This layer is not intended to silently repair the known upstream timestamp/category warnings.
8. **The SQL checks are supplementary.** `src/quality_checks.py` remains the authoritative 31-rule Silver-quality implementation. Nonzero Gold model checks stop the analytics runner.
9. **Orders without items are counted explicitly.** Gold `fact_orders` fills a missing aggregated amount with zero. Therefore `orders_without_items` is based on `order_item_count = 0`, not `order_total_amount IS NULL`. A zero recorded amount does not prove a true zero-value transaction.

## Development and verification

- The four supplied Gold Parquet files have the expected schema and metadata row counts. Full SQL query results must be verified by executing them in the project environment before recording final business findings.
- Dataset files and generated report outputs should not be committed to Git. Commit SQL, Python and documentation, not the Parquet artifacts.

## Example findings from the verified historical snapshot

- All eight Gold integrity checks reported zero issues.
- `health_beauty` ranked first among delivered-order categories by recorded item-price value (BRL 1,233,131.72, excluding freight).
- São Paulo (SP) had 40,501 delivered orders in the customer-state analysis.
- In March 2018, 18.96% of delivered orders with comparable dates arrived after the estimated delivery date.

These figures describe the historical Olist snapshot used for testing, not live operations or accounting-recognized revenue. Small monthly denominators (for example one delivered order in September 2016) can produce unstable percentages.
