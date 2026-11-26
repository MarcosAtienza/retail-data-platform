# Local Data Pipeline

## Overview

The Retail Data Platform implements a local, reproducible data pipeline for five datasets from the Olist Brazilian e-commerce dataset. The pipeline uses Python, DuckDB, and Parquet. No active Azure subscription or cloud resources are required to run it.

```text
Original CSV files (data/raw/)
          |
          v
Bronze ingestion (src/ingest_bronze.py)
          |
          v
Bronze Parquet files (data/bronze/)
          |
          v
Silver transformation (src/transform_silver.py)
          |
          v
Silver Parquet files (data/processed/)
          |
          v
Data-quality checks and CSV report (src/generate_quality_report.py)
          |
          v
Gold modelling (src/transform_gold.py)
          |
          v
Gold Parquet files (data/gold/)
          |
          v
Gold integrity checks and SQL analytics (src/run_analytics.py)
```

The `src/run_pipeline.py` script orchestrates these five stages sequentially. A stage must finish successfully before the next starts.

## Input datasets

| Source CSV in `data/raw/` | Bronze/Silver Parquet name | Rows in verified local run |
|---|---|---:|
| `olist_orders_dataset.csv` | `orders.parquet` | 99,441 |
| `olist_order_items_dataset.csv` | `order_items.parquet` | 112,650 |
| `olist_products_dataset.csv` | `products.parquet` | 32,951 |
| `olist_customers_dataset.csv` | `customers.parquet` | 99,441 |
| `product_category_name_translation.csv` | `product_category_name_translation.parquet` | 71 |

These row counts describe one verified run; they are not hard-coded requirements for other snapshots.

## Stage 1: Bronze ingestion

**Script:** `src/ingest_bronze.py`

- Checks that all five source CSV files exist.
- Reads the source columns as strings using DuckDB.
- Writes one Parquet file per dataset into `data/bronze/`.
- Checks that each Bronze file has the same number of rows as its source CSV.
- Builds the new files in a temporary directory before replacing the existing Bronze outputs.
- Does not modify the original CSV files.

Bronze preserves source columns and parsed field values in a tabular format. It is **not** a byte-for-byte archival copy of each CSV.

## Stage 2: Silver transformation

**Script:** `src/transform_silver.py`

- Reads the five Bronze Parquet files, not the CSVs.
- Trims identifier and text fields and converts empty strings to null where defined.
- Converts date fields to timestamps and numeric fields to appropriate types using DuckDB `TRY_CAST`.
- Writes the five Silver Parquet files to `data/processed/`.
- Compares Bronze and Silver row counts for every dataset.
- Leaves Bronze and original CSV files unchanged.

`TRY_CAST` returns null when a source value cannot be converted. Row-count checks alone do not establish that every field was converted correctly; the data-quality rules provide complementary checks.

## Stage 3: Data quality

**Scripts:** `src/quality_checks.py` and `src/generate_quality_report.py`

- Checks the expected schema of all five Silver datasets.
- Executes 31 rules for keys, duplicates, references, values, timestamps, and category coverage.
- Writes `reports/data_quality/data_quality_report.csv`.
- Returns a nonzero exit code if an `ERROR` rule fails.
- Allows the pipeline to finish when only `WARNING` rules report anomalies.

Rule definitions and their counting units are documented in [`data-quality-rules.md`](data-quality-rules.md).

### Verified result

In the verified local run, **26 rules passed, 5 produced warnings, and none failed**. The overall status was `PASSED_WITH_WARNINGS`.

| Rule | Known warning | Count | Unit |
|---|---|---:|---|
| DQ-006 | Delivered orders without a recorded customer delivery date | 8 | Rows |
| DQ-007 | Carrier date before approval date | 1,359 | Rows |
| DQ-008 | Customer delivery date before carrier date | 23 | Rows |
| DQ-019 | Products without a category | 610 | Rows |
| DQ-022 | Product categories without an English translation | 2 | Distinct categories |

Anomalies are reported rather than silently corrected. Counts from different rules may overlap and must not be added to estimate unique affected records.

## Stage 4: Gold analytical models

**Script:** `src/transform_gold.py`

- Reads the five Silver Parquet files.
- Writes four models to `data/gold/`: `fact_orders`, `fact_order_items`, `dim_products`, and `dim_customers`.
- Preserves one row per order in `fact_orders` and one row per ordered item in `fact_order_items`.
- Checks output counts and key uniqueness before promotion.
- Does not change Raw, Bronze, or Silver files.

## Stage 5: Gold integrity and business SQL

**Script:** `src/run_analytics.py`

- Runs the SQL files in `sql/analytics/` in filename order.
- Requires `00_gold_model_checks.sql` to return valid, zero-issue results; nonzero issue counts stop the pipeline.
- Prints analyses of delivered-order value, categories, customer states, delivery performance, and order statuses.
- Does not write any new dataset.

Business findings and interpretation rules are documented in [`gold-analytics.md`](gold-analytics.md).

## How to run

1. Use a Python environment with the project dependencies installed (notably `duckdb` and `pandas`).
2. Ensure the five original CSV files are present under `data/raw/`.
3. From the project root, run:

```bash
python src/run_pipeline.py
```

This invokes, in order:

```text
src/ingest_bronze.py
src/transform_silver.py
src/generate_quality_report.py
src/transform_gold.py
src/run_analytics.py
```

Each script can also be run individually during development. For example, to rerun only the checks:

```bash
python src/validate_data.py
```

To regenerate the quality report without rerunning ingestion or transformations:

```bash
python src/generate_quality_report.py
```

## Failure handling and limitations

- The orchestrator stops when any stage returns a nonzero exit code.
- Warnings alone do not stop the pipeline; failed Silver `ERROR` rules or failed Gold integrity checks do.
- The stages are **not one global transaction**. If a later stage fails, an earlier successful stage is not rolled back.
- A staging directory is used before each layer's outputs are promoted, but replacing multiple files is not an all-or-nothing operation if promotion itself is interrupted.
- Row-count equality detects missing or additional rows, not arbitrary changes to field values.
- The pipeline is designed for local execution from available CSV files. It is not a scheduled production workflow and has no cloud deployment.

## Git repository policy

Source CSVs, generated Bronze/Silver/Gold Parquet files, and generated quality-report CSVs are runtime data and should be excluded from Git by `.gitignore`. Commit the source code, reproducible notebooks, and documentation instead.

## Azure context

An Azure architecture is documented as a possible future deployment target. The current implementation runs locally without Azure charges. Do not describe Azure ingestion, orchestration, or storage integration as operational or verified.
