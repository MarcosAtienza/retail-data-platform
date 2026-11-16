# Data Quality Rules

## 1. Purpose

This document defines the initial data quality rules for the Retail Data Platform project.

The purpose of these rules is to ensure that the processed data is reliable, consistent and suitable for further transformations and analytics.

The validations are implemented using Python and DuckDB against the processed Parquet files.

## 2. Scope

The initial validation process covers the following tables:

- `orders`
- `order_items`

Input files:

- `data/processed/orders.parquet`
- `data/processed/order_items.parquet`

Implementation:

- Python script: `src/validate_data.py`
- SQL engine: DuckDB

## 3. Data Quality Rules

| Rule ID | Table | Column(s) | Description | Severity |
|---|---|---|---|---|
| DQ-001 | orders | order_id | Order ID must not be null. | Error |
| DQ-002 | orders | order_id | Order ID must be unique. | Error |
| DQ-003 | order_items | order_id, order_item_id | The combination of order ID and item ID must be unique. | Error |
| DQ-004 | order_items | order_id | Every order ID in order_items must exist in orders. | Error |
| DQ-005 | order_items | price | Price must not be negative. | Error |
| DQ-006 | order_items | freight_value | Freight value must not be negative. | Error |
| DQ-007 | orders | Timestamp columns | Date columns must have the expected TIMESTAMP data type. | Error |
| DQ-008 | orders | Order timestamps | Actual order dates must follow a consistent chronological sequence. | Error |
| DQ-009 | orders | Delivery timestamps | Missing dates must be evaluated according to the order status. | Warning |
| DQ-010 | orders | order_estimated_delivery_date | Estimated delivery date must not precede purchase date. | Warning |

## 4. Validation Details

### 4.1. Primary Key Validation

The `orders` table must contain one unique, non-null `order_id` per order.

The `order_items` table uses a composite key:

- `order_id`
- `order_item_id`

This is necessary because an order can contain multiple items.

### 4.2. Referential Integrity

Every `order_id` in `order_items` must have a corresponding record in `orders`.

Orphan records indicate that an order item references an order that does not exist in the parent table.

### 4.3. Numeric Validation

The following conditions are expected:

- `price` must be greater than or equal to zero.
- `freight_value` must be greater than or equal to zero.

Negative values must be investigated before the data is considered reliable.

### 4.4. Timestamp Validation

The following columns in `orders` are expected to have the `TIMESTAMP` data type:

- `order_purchase_timestamp`
- `order_approved_at`
- `order_delivered_carrier_date`
- `order_delivered_customer_date`
- `order_estimated_delivery_date`

The actual order lifecycle should follow this chronological sequence when the relevant dates are available:

1. Purchase timestamp.
2. Approval timestamp.
3. Carrier delivery timestamp.
4. Customer delivery timestamp.

The estimated delivery date is a prediction rather than an actual event. It is therefore validated separately.

### 4.5. Missing Dates and Order Status

Missing timestamps are not automatically considered data quality errors.

Their validity depends on the order status and lifecycle.

For example:

- A cancelled order may not have a delivery date.
- An order that has not yet been delivered may not have a customer delivery date.
- Some orders may not have reached the approval or shipping stages.

Missing dates should therefore be evaluated using the corresponding `order_status`.

## 5. Severity Levels

Two severity levels are defined:

**Error**

A violation that indicates a potential integrity or consistency problem. It requires investigation before the affected data is considered reliable.

**Warning**

An unusual or incomplete value that may be legitimate depending on the business context. It should be reviewed but does not necessarily prevent the pipeline from continuing.

## 6. Validation Approach

The validation process follows these steps:

1. Read the processed Parquet files using DuckDB.
2. Execute SQL queries for each data quality rule.
3. Count the records that violate each rule.
4. Classify the result as PASS or FAIL.
5. Review failed checks and investigate their causes.

The initial implementation is designed to validate the local Silver-like data layer.

## 7. Future Improvements

The following improvements are planned for future iterations:

- Generate a structured data quality report for each pipeline execution.
- Store validation results with execution timestamps.
- Separate critical errors from non-blocking warnings.
- Prevent unreliable data from being promoted to the Gold layer.
- Add automated tests for transformation and validation logic.
- Integrate data quality checks into the complete ingestion and transformation workflow.

## 8. Notes

These rules represent the initial technical assumptions for the Retail Data Platform project.

In a production environment, business-specific validation rules should be confirmed with the relevant business stakeholders before being treated as definitive data quality requirements.