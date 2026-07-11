from pathlib import Path
import pandas as pd
import numpy as np


RAW_FILE = Path("data/raw/online_retail.xlsx")
CLEAN_DIR = Path("data/cleaned")
REPORT_DIR = Path("reports/data_quality")


def most_common_value(series: pd.Series) -> str:
    """
    Return the most common non-null value from a pandas Series.
    If no valid value exists, return UNKNOWN_DESCRIPTION.

    A product code may appear many times with the same description.
    We use the most frequent description to build a product master table.
    """
    cleaned = series.dropna().astype(str).str.strip()
    cleaned = cleaned[cleaned != ""]

    if cleaned.empty:
        return "UNKNOWN_DESCRIPTION"

    return cleaned.mode().iloc[0]


def load_raw_data() -> pd.DataFrame:
    """
    Load the raw Excel file.

    This keeps the raw file untouched and returns a DataFrame for cleaning.
    """
    if not RAW_FILE.exists():
        raise FileNotFoundError(
            f"Raw file not found: {RAW_FILE}. "
            "Make sure online_retail.xlsx exists in data/raw/"
        )

    print("Loading raw Online Retail dataset...")
    df = pd.read_excel(RAW_FILE)

    print(f"Raw rows loaded: {len(df):,}")
    print(f"Raw columns loaded: {len(df.columns)}")

    return df


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename raw columns into snake_case.

    Snake_case column names are easier to use in Python, SQL, and dashboards.
    """
    column_map = {
        "InvoiceNo": "invoice_no",
        "StockCode": "stock_code",
        "Description": "description",
        "Quantity": "quantity",
        "InvoiceDate": "invoice_date",
        "UnitPrice": "unit_price",
        "CustomerID": "customer_id",
        "Country": "country",
    }

    df = df.rename(columns=column_map)

    return df


def clean_transaction_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and enrich the transaction-level dataset.
    """
    df = df.copy()

    # Create a raw row ID so we can trace cleaned rows back to original row position.
    df.insert(0, "raw_row_id", range(1, len(df) + 1))

    # Standardize text columns.
    df["invoice_no"] = df["invoice_no"].astype(str).str.strip()
    df["stock_code"] = df["stock_code"].astype(str).str.strip()
    df["country"] = df["country"].astype(str).str.strip()

    # Clean product description.
    df["description"] = df["description"].fillna("UNKNOWN_DESCRIPTION")
    df["description"] = df["description"].astype(str).str.strip()
    df.loc[df["description"] == "", "description"] = "UNKNOWN_DESCRIPTION"

    # CustomerID often has missing values and may be read as float.
    # We preserve missing customers as UNKNOWN instead of deleting them.
    df["has_customer_id"] = df["customer_id"].notna()

    def clean_customer_id(value):
        if pd.isna(value):
            return "UNKNOWN"
        try:
            return str(int(value))
        except ValueError:
            return str(value).strip()

    df["customer_id"] = df["customer_id"].apply(clean_customer_id)

    # Convert dates safely.
    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")

    # Ensure numeric columns are numeric.
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")

    # Data quality helper flags.
    df["is_cancelled_invoice"] = df["invoice_no"].str.startswith("C", na=False)
    df["is_negative_quantity"] = df["quantity"] < 0
    df["is_zero_quantity"] = df["quantity"] == 0
    df["is_missing_description"] = df["description"].eq("UNKNOWN_DESCRIPTION")
    df["is_missing_customer_id"] = df["customer_id"].eq("UNKNOWN")
    df["is_invalid_invoice_date"] = df["invoice_date"].isna()
    df["is_zero_or_negative_unit_price"] = df["unit_price"].fillna(0) <= 0

    # Duplicate rows based on raw business fields.
    duplicate_subset = [
        "invoice_no",
        "stock_code",
        "description",
        "quantity",
        "invoice_date",
        "unit_price",
        "customer_id",
        "country",
    ]
    df["is_duplicate_row"] = df.duplicated(subset=duplicate_subset, keep=False)

    # Transaction status logic.
    conditions = [
        df["is_cancelled_invoice"] | df["is_negative_quantity"],
        df["is_zero_quantity"] | df["is_zero_or_negative_unit_price"] | df["is_invalid_invoice_date"],
    ]

    choices = [
        "Cancelled/Return",
        "Data Issue",
    ]

    df["transaction_status"] = np.select(
        conditions,
        choices,
        default="Completed"
    )

    # Financial fields.
    df["line_revenue"] = df["quantity"] * df["unit_price"]

    df["completed_sales_amount"] = np.where(
        df["transaction_status"] == "Completed",
        df["line_revenue"],
        0
    )

    df["cancelled_amount"] = np.where(
        df["transaction_status"] == "Cancelled/Return",
        df["line_revenue"].abs(),
        0
    )

    # Date fields for reporting.
    df["invoice_year"] = df["invoice_date"].dt.year
    df["invoice_month"] = df["invoice_date"].dt.month
    df["invoice_day"] = df["invoice_date"].dt.day
    df["invoice_hour"] = df["invoice_date"].dt.hour
    df["invoice_year_month"] = df["invoice_date"].dt.to_period("M").astype(str)

    # Reorder columns for readability.
    column_order = [
        "raw_row_id",
        "invoice_no",
        "stock_code",
        "description",
        "quantity",
        "invoice_date",
        "unit_price",
        "customer_id",
        "has_customer_id",
        "country",
        "transaction_status",
        "line_revenue",
        "completed_sales_amount",
        "cancelled_amount",
        "invoice_year",
        "invoice_month",
        "invoice_day",
        "invoice_hour",
        "invoice_year_month",
        "is_cancelled_invoice",
        "is_negative_quantity",
        "is_zero_quantity",
        "is_missing_description",
        "is_missing_customer_id",
        "is_invalid_invoice_date",
        "is_zero_or_negative_unit_price",
        "is_duplicate_row",
    ]

    df = df[column_order]

    return df


def create_products_table(transactions: pd.DataFrame) -> pd.DataFrame:
    """
    Create a product master-style table from transaction data.

    BI dashboards usually benefit from separate dimension/master tables.
    """
    products = (
        transactions
        .groupby("stock_code")
        .agg(
            product_description=("description", most_common_value),
            product_category=("description", lambda x: "Retail Product"),
            avg_unit_price=("unit_price", "mean"),
            min_unit_price=("unit_price", "min"),
            max_unit_price=("unit_price", "max"),
            transaction_line_count=("raw_row_id", "count"),
            completed_line_count=("transaction_status", lambda x: (x == "Completed").sum()),
        )
        .reset_index()
    )

    products["avg_unit_price"] = products["avg_unit_price"].round(2)
    products["min_unit_price"] = products["min_unit_price"].round(2)
    products["max_unit_price"] = products["max_unit_price"].round(2)

    return products


def create_customers_table(transactions: pd.DataFrame) -> pd.DataFrame:
    """
    Create a customer master-style table.

    This lets us analyze customer coverage and country-level behavior later.
    """
    known_customers = transactions[transactions["customer_id"] != "UNKNOWN"].copy()

    customers = (
        known_customers
        .groupby("customer_id")
        .agg(
            country=("country", most_common_value),
            first_invoice_date=("invoice_date", "min"),
            last_invoice_date=("invoice_date", "max"),
            transaction_line_count=("raw_row_id", "count"),
            completed_sales_amount=("completed_sales_amount", "sum"),
            cancelled_amount=("cancelled_amount", "sum"),
        )
        .reset_index()
    )

    customers["completed_sales_amount"] = customers["completed_sales_amount"].round(2)
    customers["cancelled_amount"] = customers["cancelled_amount"].round(2)

    return customers


def create_data_quality_issue_log(transactions: pd.DataFrame) -> pd.DataFrame:
    """
    Create a row-level issue log.
    """
    issue_frames = []

    def add_issue(mask, issue_type, issue_description):
        issues = transactions.loc[mask, [
            "raw_row_id",
            "invoice_no",
            "stock_code",
            "description",
            "customer_id",
            "country",
            "transaction_status",
        ]].copy()

        issues["issue_type"] = issue_type
        issues["issue_description"] = issue_description

        issue_frames.append(issues)

    add_issue(
        transactions["is_missing_customer_id"],
        "Missing Customer ID",
        "CustomerID was missing in the raw dataset and was standardized as UNKNOWN."
    )

    add_issue(
        transactions["is_missing_description"],
        "Missing Description",
        "Product description was missing and was standardized as UNKNOWN_DESCRIPTION."
    )

    add_issue(
        transactions["is_cancelled_invoice"],
        "Cancelled Invoice",
        "Invoice number begins with C, indicating a cancellation."
    )

    add_issue(
        transactions["is_negative_quantity"],
        "Negative Quantity",
        "Quantity is negative, indicating a return/cancellation or source system adjustment."
    )

    add_issue(
        transactions["is_zero_quantity"],
        "Zero Quantity",
        "Quantity is zero and needs review before reporting."
    )

    add_issue(
        transactions["is_zero_or_negative_unit_price"],
        "Zero or Negative Unit Price",
        "Unit price is zero or negative and should be excluded from revenue KPIs."
    )

    add_issue(
        transactions["is_invalid_invoice_date"],
        "Invalid Invoice Date",
        "Invoice date could not be converted to a valid datetime."
    )

    add_issue(
        transactions["is_duplicate_row"],
        "Duplicate Row",
        "Row appears to be duplicated based on core transaction fields."
    )

    if not issue_frames:
        return pd.DataFrame(columns=[
            "raw_row_id",
            "invoice_no",
            "stock_code",
            "description",
            "customer_id",
            "country",
            "transaction_status",
            "issue_type",
            "issue_description",
        ])

    issue_log = pd.concat(issue_frames, ignore_index=True)

    issue_log = issue_log.sort_values(
        by=["raw_row_id", "issue_type"]
    ).reset_index(drop=True)

    return issue_log


def create_cleaning_summary(raw_df: pd.DataFrame, transactions: pd.DataFrame, issue_log: pd.DataFrame) -> pd.DataFrame:
    """
    Create a cleaning summary report with important counts.
    """
    summary_items = {
        "raw_rows": len(raw_df),
        "cleaned_transaction_rows": len(transactions),
        "total_columns_cleaned": len(transactions.columns),
        "completed_rows": int((transactions["transaction_status"] == "Completed").sum()),
        "cancelled_return_rows": int((transactions["transaction_status"] == "Cancelled/Return").sum()),
        "data_issue_rows": int((transactions["transaction_status"] == "Data Issue").sum()),
        "missing_customer_id_rows": int(transactions["is_missing_customer_id"].sum()),
        "missing_description_rows": int(transactions["is_missing_description"].sum()),
        "duplicate_rows": int(transactions["is_duplicate_row"].sum()),
        "zero_or_negative_unit_price_rows": int(transactions["is_zero_or_negative_unit_price"].sum()),
        "unique_invoice_count": int(transactions["invoice_no"].nunique()),
        "unique_product_count": int(transactions["stock_code"].nunique()),
        "known_customer_count": int(transactions.loc[transactions["customer_id"] != "UNKNOWN", "customer_id"].nunique()),
        "country_count": int(transactions["country"].nunique()),
        "data_quality_issue_records": len(issue_log),
        "total_completed_sales_amount": round(transactions["completed_sales_amount"].sum(), 2),
        "total_cancelled_amount": round(transactions["cancelled_amount"].sum(), 2),
    }

    summary = pd.DataFrame(
        [{"metric": key, "value": value} for key, value in summary_items.items()]
    )

    return summary


def save_outputs(
    transactions: pd.DataFrame,
    products: pd.DataFrame,
    customers: pd.DataFrame,
    issue_log: pd.DataFrame,
    cleaning_summary: pd.DataFrame
) -> None:
    """
    Save all cleaned outputs.
    """
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    transactions.to_csv(CLEAN_DIR / "online_retail_transactions_cleaned.csv", index=False)
    products.to_csv(CLEAN_DIR / "products_cleaned.csv", index=False)
    customers.to_csv(CLEAN_DIR / "customers_cleaned.csv", index=False)

    issue_log.to_csv(REPORT_DIR / "data_quality_issues.csv", index=False)
    cleaning_summary.to_csv(REPORT_DIR / "cleaning_summary.csv", index=False)

    print("\nSaved cleaned outputs:")
    print(f"- {CLEAN_DIR / 'online_retail_transactions_cleaned.csv'}")
    print(f"- {CLEAN_DIR / 'products_cleaned.csv'}")
    print(f"- {CLEAN_DIR / 'customers_cleaned.csv'}")
    print(f"- {REPORT_DIR / 'data_quality_issues.csv'}")
    print(f"- {REPORT_DIR / 'cleaning_summary.csv'}")


def main():
    raw_df = load_raw_data()
    standardized_df = standardize_columns(raw_df)

    transactions = clean_transaction_data(standardized_df)
    products = create_products_table(transactions)
    customers = create_customers_table(transactions)
    issue_log = create_data_quality_issue_log(transactions)
    cleaning_summary = create_cleaning_summary(raw_df, transactions, issue_log)

    save_outputs(
        transactions=transactions,
        products=products,
        customers=customers,
        issue_log=issue_log,
        cleaning_summary=cleaning_summary
    )

    print("\n=== Cleaning Summary ===")
    print(cleaning_summary.to_string(index=False))

    print("\nData cleaning completed successfully.")


if __name__ == "__main__":
    main()