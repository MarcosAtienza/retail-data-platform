# Data Dictionary — Olist processed datasets

These are expected source-style names; adjust if your Silver transformations renamed columns.

| Dataset | Grain | Primary/composite key | Foreign keys |
|---|---|---|---|
| `orders` | One order | `order_id` | `customer_id` → `customers.customer_id` |
| `order_items` | One item within an order | (`order_id`, `order_item_id`) | `order_id` → orders; `product_id` → products |
| `products` | One product | `product_id` | `product_category_name` → category translation (optional) |
| `customers` | One customer record | `customer_id` | Referenced by orders |
| `product_category_name_translation` | One source category | `product_category_name` | Referenced by products |

## orders.parquet

| Column | Meaning |
|---|---|
| `order_id` | Order identifier |
| `customer_id` | Customer record identifier |
| `order_status` | Order lifecycle status |
| `order_purchase_timestamp` | Purchase time |
| `order_approved_at` | Approval time |
| `order_delivered_carrier_date` | Carrier handoff time |
| `order_delivered_customer_date` | Customer delivery time |
| `order_estimated_delivery_date` | Estimated delivery time |

## order_items.parquet

| Column | Meaning |
|---|---|
| `order_id` | Parent order |
| `order_item_id` | Item sequence number within order |
| `product_id` | Product reference |
| `seller_id` | Seller reference (seller table not in scope) |
| `shipping_limit_date` | Seller shipping deadline |
| `price` | Item price |
| `freight_value` | Item freight value |

## products.parquet

| Column | Meaning |
|---|---|
| `product_id` | Product identifier |
| `product_category_name` | Source category |
| `product_name_lenght` | Product name length; source spelling retained |
| `product_description_lenght` | Description length; source spelling retained |
| `product_photos_qty` | Number of product photos |
| `product_weight_g` | Weight in grams |
| `product_length_cm` | Length in centimetres |
| `product_height_cm` | Height in centimetres |
| `product_width_cm` | Width in centimetres |

## customers.parquet

| Column | Meaning |
|---|---|
| `customer_id` | Customer record identifier used in orders |
| `customer_unique_id` | Identifier grouping customer records across orders |
| `customer_zip_code_prefix` | Brazilian postal code prefix |
| `customer_city` | City |
| `customer_state` | State abbreviation |

## product_category_name_translation.parquet

| Column | Meaning |
|---|---|
| `product_category_name` | Source category name |
| `product_category_name_english` | English category name |

## Modelling cautions

- Join orders to items on `order_id`, items to products on `product_id`, orders to customers on `customer_id`.
- Join product categories to translations on `product_category_name`.
- `customer_unique_id` is not the key used by the orders-to-customers relationship.
- Avoid duplicating order-level metrics after joining orders to multiple item rows.
