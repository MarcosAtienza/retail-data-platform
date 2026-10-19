# 1. Overview

This document describes the source data model used in the Retail Data Platform project.

The project uses the Brazilian E-Commerce Public Dataset by Olist, which contains information about orders, customers, products, and order items from a Brazilian e-commerce marketplace.

The initial implementation focuses on five source files:

olist_orders_dataset.csv

olist_order_items_dataset.csv

olist_customers_dataset.csv

olist_products_dataset.csv

product_category_name_translation.csv

The source tables will be preserved in their original form. Data cleaning, type standardization, validation, and analytical modeling will be performed in downstream processing layers.

# 2. Source Data Model

## 2.1. orders

Source: olist_orders_dataset.csv

Grain: One row per order.

Primary key: order_id

This table contains order-level information, including the associated customer, order status, purchase timestamp, and delivery timestamps.

Key relationships:

- customer_id references customers.customer_id.
- order_id is referenced by order_items.order_id.

## 2.2. customers

Source: olist_customers_dataset.csv

Grain: One row per customer record associated with an order.

Primary key: customer_id

Key relationships:

- customer_id is referenced by orders.customer.id.

This table contains customer identifiers and geographic information.

## 2.3. order_items

Source: olist_order_items_dataset.csv

Grain: One row per order item, identified by the combination of order_id and order_item_id.

Composite primary key: (order_id, order_item_id)

Key relationships:

- order_id references orders.order_id.
- product_id references products.product_id.

## 2.4. products

Source: olist_products_dataset.csv

Grain: One row per product.

Primary key: product_id

This table contains product categories, descriptive attributes, and physical dimensions.

Key relationships:

- product_category_name references the corresponding category in product_category_name_translation.
- product_id is referenced by order_items.product_id

## 2.5. product_category_name_translation

Source: product_category_name_translation.csv

Grain: One row per translated category.

Candidate primary key: product_category_name

The relationship with products is many-to-one: multiple products may belong to the same category.

Key relations:

- product_category_name is referenced by products.product_category_name

# 3. Main relationships

The main relationships between the source tables are:

+=======================================================================================================+
| Table                               | Child table      | Relationship        | Join condition         |
+=======================================================================================================+
| customers                           | orders           | one-to-many         | customer_id            |
+-------------------------------------------------------------------------------------------------------+
| orders                              | order_items      | one-to-many         | order_id               |
+-------------------------------------------------------------------------------------------------------+
| products                            | order_items      | one-to-many         | product_id             |
+-------------------------------------------------------------------------------------------------------+
| product_cattegory_name_translation  | products         | Seller information  | product_category_name  |
+-------------------------------------------------------------------------------------------------------+

# 4. Data modeling rules

## 4.1. Preserve source data

Raw CSV files must remain unchanged. Parsing, renaming, standardization, deduplication, and validation will be performed in downstream layers.

## 4.2. Respect table grain

Each table must retain its defined level of detail as per section "2. Source Data Model".

## 4.3. Distinguish customer idenfifiers

Use customer_id to join orders with customers.
Use customer_unique_id when analyzing underlying customers or repeat purchases.

## 4.4. Avoid double-counting

Joining tables with one-to-many relationships can increase the number of rows.

Sales calculations must use the appropriate grain and must not aggregate duplicated order-item records. Additional one-to-many datasets, such as payments or reviews, must be modeled carefully if introduced later.

## 4.5. Standarize data types downstream

Identifiers should generally be represented as strings. Monetary values should use an appropriate decimal type, and date/time fields should use suitable date or timestamp types.

Postal code prefixes should remain strings to preserve leading zeros.

## 4.5. Validate relationships and data quality

Downstream processing should check:

- Duplicate primary or candidate keys.
- Missing required identifiers.
- Invalid or unparseable dates.
- Unexpected null values.
- Orphan records that do not match the expected parent table.
- Invalid or missing product category translations.

Data quality rules and their outcomes will be documented as the pipeline evolves.

# 5. Planned analytical model

The source model will later be transformed into a dimensional model for analytical queries and Power BI reporting.

The initial Gold layer is expected to contain:

+===========================================================================================+
| Table         | Planned grain           | Purpose                                         |
+===========================================================================================+
| fact_sales    | One row per order item  | Analyze sales, item prices and freight values   |
+-------------------------------------------------------------------------------------------+
| dim_customer  | One row per customer    | Analyze customer characteristics and geography  |
+-------------------------------------------------------------------------------------------+
| dim_product   | One row per product     | Analyze products and translated categories      |+-------------------------------------------------------------------------------------------+
| dim_date      | One row calendar day    | Enable time-based analysis                      |
+-------------------------------------------------------------------------------------------+
