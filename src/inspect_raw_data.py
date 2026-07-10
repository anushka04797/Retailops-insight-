from pathlib import Path
import pandas as pd

RAW_FILE = Path("data/raw/online_retail.xlsx")

def main():
    if not RAW_FILE.exists():
        raise FileNotFoundError(f"Raw dataset not found: {RAW_FILE}")

    print("Reading raw Online Retail dataset...")
    df = pd.read_excel(RAW_FILE)

    print("\n=== Dataset Shape ===")
    print(f"Rows: {df.shape[0]:,}")
    print(f"Columns: {df.shape[1]}")

    print("\n=== Column Names ===")
    print(df.columns.tolist())

    print("\n=== First 5 Rows ===")
    print(df.head())

    print("\n=== Missing Values ===")
    print(df.isna().sum())

    print("\n=== Data Types ===")
    print(df.dtypes)

    print("\nRaw data inspection completed successfully.")

if __name__ == "__main__":
    main()