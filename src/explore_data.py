from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "raw"

files = [
    "olist_customers_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_products_dataset.csv",
    "product_category_name_translation.csv",
]

for file in files:
    file_path = DATA_PATH / file

    df = pd.read_csv(file_path)

    print(f"\n{'=' * 50}")
    print(f"FILE: {file}")
    print(f"ROWS: {df.shape[0]}")
    print(f"COLUMNS: {df.shape[1]}")

    print("\nColumn names:")
    print(df.columns.tolist())

    print("\nFirst 5 rows:")
    print(df.head())

    print("\nMissing values:")
    print(df.isnull().sum())
