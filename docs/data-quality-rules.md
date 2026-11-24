# Data Quality Rules

31 automated checks for five processed Olist datasets. Run `python src/validate_data.py` for console results and `python src/generate_quality_report.py` for a CSV in `reports/data_quality/data_quality_report.csv`.

**ERROR** checks produce `FAIL` when problems exist; **WARNING** checks produce `WARNING`. Overall status is `FAILED`, `PASSED_WITH_WARNINGS`, or `PASSED`.

A count can represent rows, duplicate-key groups, or distinct category values. Different rules can count the same row. Checks never modify source data.

The expected schema is verified before running SQL. Rules assume all five Parquet files represent the same processing snapshot.

## Orders

| Rule | Check | Severity | Counting unit |
|---|---|---|---|
| DQ-001 | Null order IDs | ERROR | Rows |
| DQ-002 | Duplicate order IDs | ERROR | Duplicate key groups |
| DQ-003 | Null customer IDs in orders | ERROR | Rows |
| DQ-004 | Invalid order statuses | ERROR | Rows |
| DQ-005 | Approval before purchase | ERROR | Rows |
| DQ-006 | Delivered orders missing delivery timestamp | WARNING | Rows |
| DQ-007 | Carrier timestamp before approval | WARNING | Rows |
| DQ-008 | Customer delivery before carrier timestamp | WARNING | Rows |
| DQ-009 | Orders with unknown customer | ERROR | Rows |

## Order Items

| Rule | Check | Severity | Counting unit |
|---|---|---|---|
| DQ-010 | Null order or item IDs | ERROR | Rows |
| DQ-011 | Duplicate order-item keys | ERROR | Duplicate key groups |
| DQ-012 | Order items with unknown order | ERROR | Rows |
| DQ-013 | Order items with missing or unknown product | ERROR | Rows |
| DQ-014 | Negative item prices | ERROR | Rows |
| DQ-015 | Negative freight values | ERROR | Rows |
| DQ-016 | Null item price or freight | ERROR | Rows |

## Products

| Rule | Check | Severity | Counting unit |
|---|---|---|---|
| DQ-017 | Null product IDs | ERROR | Rows |
| DQ-018 | Duplicate product IDs | ERROR | Duplicate key groups |
| DQ-019 | Products without category | WARNING | Rows |
| DQ-020 | Negative product weight or dimensions | ERROR | Rows |
| DQ-021 | Negative product text lengths or photo count | ERROR | Rows |
| DQ-022 | Product categories without translation | WARNING | Distinct category values |

## Customers

| Rule | Check | Severity | Counting unit |
|---|---|---|---|
| DQ-023 | Null customer IDs | ERROR | Rows |
| DQ-024 | Duplicate customer IDs | ERROR | Duplicate key groups |
| DQ-025 | Null customer unique IDs | ERROR | Rows |
| DQ-026 | Customers with missing city or state | WARNING | Rows |
| DQ-027 | Invalid state code length | WARNING | Rows |

## Category Translation

| Rule | Check | Severity | Counting unit |
|---|---|---|---|
| DQ-028 | Null source categories in translation | ERROR | Rows |
| DQ-029 | Duplicate source categories in translation | ERROR | Duplicate key groups |
| DQ-030 | Missing English translation | ERROR | Rows |
| DQ-031 | Unused translation categories | WARNING | Distinct category values |

## Notes

- DQ-004 accepts the eight observed source statuses, including `created`.
- DQ-027 checks Brazilian state abbreviations for two characters.
- `product_name_lenght` and `product_description_lenght` retain the original Olist spelling.
- Temporal anomalies are reported without automatic correction.
- Null numeric product attributes are profiled in the notebook; DQ-020/021 only flag negative non-null values.
- A PASS does not establish complete data correctness.
