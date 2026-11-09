# Initial Data Exploration

## Dataset
Brazilian E-Commerce Public Dataset by Olist

## Source tables
- Customers
- Orders
- Order items
- Products
- Product category translation

## Initial observations
- Total orders: 99,441
- Total order items: 112,650
- Most common order status: delivered
- Missing values identified in several columns.

## Data structure findings
- One order can contain multiple order items.
- order_id identifies an order.
- (order_id, order_item_id) identifies an order item.
- customer_id connects orders with customers.
- product_id connects order items with products.

## Initial data quality considerations
- Check duplicate primary keys.
- Validate foreign key relationships.
- Investigate missing values.
- Validate date and numeric formats.

## Design decisions
- Preserve original source data in Bronze.
- Apply cleaning and validation in Silver.
- Build analytical models in Gold.
