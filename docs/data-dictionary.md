# Dataset overview

The Brazilian E-Commerce Public Dataset by Olist contains
anonymized marketplace transactions from Brazil, covering
approximately September 2016 to August 2018. This project
uses 5 of the 9 files that form the entire dataset. This
dictionary explains the source columns of said files.

## Column-by-column dictionary

### olist_customers_dataset.csv

Customer records and customer location

+======================================================================================================+
| Column                   | Typical type | Use                                                        |
+======================================================================================================+
| customer_id              | String       | Identifier for the customer record associated with an      |
|                          |              | order; joins to orders.                                    |
+------------------------------------------------------------------------------------------------------+
| customer_unique_id       | String       | Persistent identifier for the real customer across orders; |
|                          |              | useful for repeat-purchase analysis.                       |
+------------------------------------------------------------------------------------------------------+
| customer_zip_code_prefix | String       | First five digits of the customer's Brazilian              |
|                          |              | postal code; keep as text to preserve leading zeros.       |
+------------------------------------------------------------------------------------------------------+
| customer_city            | String       | Customer city.                                             |
|                          |              |                                                            |
+------------------------------------------------------------------------------------------------------+
| customer_state           | String       | Two-letter Brazilian state abbreviation.                   |
|                          |              |                                                            |
+------------------------------------------------------------------------------------------------------+

### olist_order_items_dataset.csv

Line items with each order

+======================================================================================================+
| Column                   | Typical type | Use                                                        |
+======================================================================================================+
| order_id                 | String       | Order identifier; joins to the orders table.               |
|                          |              |                                                            |
+------------------------------------------------------------------------------------------------------+
| order_item_id            | Integer      | Sequence number for an item line within an order; together |
|                          |              | with order_id forms the practical line key.                |
+------------------------------------------------------------------------------------------------------+
| product_id               | String       | Product identifier; joins to products.                     |
|                          |              |                                                            |
+------------------------------------------------------------------------------------------------------+
| seller_id                | String       | Seller identifier; joins to sellers.                       |
|                          |              |                                                            |
+------------------------------------------------------------------------------------------------------+
| shipping_limit_date      | Datetime     | Deadline by which the seller should hand the item to the   |
|                          |              | carrier.                                                   |
+------------------------------------------------------------------------------------------------------+
| price                    | Decimal      | Price of the product line, excluding freight.              |
|                          |              |                                                            |
+------------------------------------------------------------------------------------------------------+
| freight_value            | Decimal      | Shipping/freight amount allocated to this item.            |
|                          |              |                                                            |
+------------------------------------------------------------------------------------------------------+

### olist_orders_dataset.csv

Order header and lifecycle timestamps.

+======================================================================================================+
| Column                   | Typical type | Use                                                        |
+======================================================================================================+
| order_id                 | String       | Unique order identifier.                                   |
|                          |              |                                                            |
+------------------------------------------------------------------------------------------------------+
| customer_id              | String       | Customer record identifier; joins to customers.            |
|                          |              |                                                            |
+------------------------------------------------------------------------------------------------------+
| order_status             | String       | Order lifecycle status (delivered, shipped, canceled,      |
|                          |              | processing or unavailable).                                |
+------------------------------------------------------------------------------------------------------+
| order_purchase_timestamp | Datetime     | Date/time when the customer placed the order.              |
|                          |              |                                                            |
+------------------------------------------------------------------------------------------------------+
| order_approved_at        | Datetime     | Date/time when the order/payment was approved; may be      |
|                          |              | null.                                                      |
+------------------------------------------------------------------------------------------------------+
| order_delivered_carrier_ | Datetime     | Date/time the order was handed to the logistics carrier;   |
| date                     |              | may be null.                                               |
+------------------------------------------------------------------------------------------------------+
| order_delivered_customer | Datetime     | Date/time when the order was delivered to the customer;    |
| _date                    |              | may be null.                                               |
+------------------------------------------------------------------------------------------------------+
| order_estimated_delivery | Datetime     | Estimated delivery date communicated to the customer.      |
| _date                    |              |                                                            |
+------------------------------------------------------------------------------------------------------+

### olist_products_dataset.csv

Product catalogue attributes and physical dimensions.

+======================================================================================================+
| Column                   | Target type  | Use                                                        |
+======================================================================================================+
| product_id               | String       | Unique product identifier.                                 |
|                          |              |                                                            |
+------------------------------------------------------------------------------------------------------+
| product_category_name    | String       | Product category name. generally in Portuguese; can join   |
|                          |              | to category translation.                                   |
+------------------------------------------------------------------------------------------------------+
| product_name_lenght      | Numeric      | Number of characters in the product name. Original source  |
|                          |              | spelling is "lenght".                                      |
+------------------------------------------------------------------------------------------------------+
| product_description      | Numeric      | Number of characters in the product description. Original  |
| _lenght                  |              | source spelling is "lenght".                               |
+------------------------------------------------------------------------------------------------------+
| product_photos_qty       | Numeric      | Number of photos published for the product.                |
|                          |              |                                                            |
+------------------------------------------------------------------------------------------------------+
| product_weight_g         | Numeric      | Product weight in grams.                                   |
|                          |              |                                                            |
+------------------------------------------------------------------------------------------------------+
| product_length_cm        | Numeric      | Product length in centimeters.                             |
|                          |              |                                                            |
+------------------------------------------------------------------------------------------------------+
| product_height_cm        | Numeric      | Product height in centimeters.                             |
|                          |              |                                                            |
+------------------------------------------------------------------------------------------------------+
| product_width_cm         | Numeric      | Product width in centimeters.                              |
|                          |              |                                                            |
+------------------------------------------------------------------------------------------------------+

### product_category_name_translation.csv

+======================================================================================================+
| Column                   | Target type  | Use                                                        |
+======================================================================================================+
| product_category_name    | String       | Product category name in Portuguese; join key to the       |
|                          |              | products table.                                            |
+------------------------------------------------------------------------------------------------------+
| product_category_name    | String       | English translation of the product category.               |
| _english                 |              |                                                            |
+------------------------------------------------------------------------------------------------------+

## Main relationships

- customers.customer_id 1 -> N orders.customer_id
- orders.order_id 1 -> N order_items.order_id
- products.product_id 1 -> N order_items.product_id
- products.product_category_name 1 -> 1 product_category_name_translation.product_category_name

## Grain and modelling notes

- Orders: one row per order_id.
- Order items: one row per order_id + order_item_id. Do not treat order_id alone as unique in this file.
- Postal code prefixes are identifiers, not measures; must be sored as strings so leading zeros are preserved.
- Raw source CSVs must be preserved unchanged. Parsing, standardization, deduplication and validation must be
applied in a downstream clean/staging layer.

## Source and reference

Original dataset page: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
Schema reference used for this documentation: https://github.com/zeesshhaannss/Olist-E-Commerce-Dashboard/blob/main/Data_Dictionary.md
