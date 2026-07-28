from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

TRANSACTIONS_SAMPLE_FILE = (
    PROJECT_ROOT / "data" / "cleaned" / "online_retail_transactions_cleaned_sample.csv"
)

PRODUCTS_FILE = (
    PROJECT_ROOT / "data" / "cleaned" / "products_cleaned.csv"
)

CUSTOMERS_FILE = (
    PROJECT_ROOT / "data" / "cleaned" / "customers_cleaned.csv"
)

CLEANING_SUMMARY_FILE = (
    PROJECT_ROOT / "reports" / "data_quality" / "cleaning_summary.csv"
)

EXECUTIVE_KPI_FILE = (
    PROJECT_ROOT / "reports" / "sql_outputs" / "executive_kpi_summary.csv"
)


def test_required_cleaned_files_exist():
    """
    Confirm that GitHub-safe cleaned and reporting files exist.
    """
    required_files = [
        TRANSACTIONS_SAMPLE_FILE,
        PRODUCTS_FILE,
        CUSTOMERS_FILE,
        CLEANING_SUMMARY_FILE,
        EXECUTIVE_KPI_FILE,
    ]

    for file_path in required_files:
        assert file_path.exists(), f"Missing required file: {file_path}"


def test_transactions_sample_has_expected_columns():
    """
    Confirm that the cleaned transaction sample has the columns needed
    for reporting, SQL analysis, and KPI calculations.
    """
    transactions = pd.read_csv(TRANSACTIONS_SAMPLE_FILE)

    expected_columns = {
        "raw_row_id",
        "invoice_no",
        "stock_code",
        "description",
        "quantity",
        "invoice_date",
        "unit_price",
        "customer_id",
        "country",
        "transaction_status",
        "line_revenue",
        "completed_sales_amount",
        "cancelled_amount",
        "invoice_year_month",
        "is_missing_customer_id",
        "is_duplicate_row",
    }

    actual_columns = set(transactions.columns)

    missing_columns = expected_columns - actual_columns

    assert not missing_columns, f"Missing columns: {missing_columns}"


def test_transactions_sample_is_not_empty():
    """
    Confirm that the transaction sample contains rows.
    """
    transactions = pd.read_csv(TRANSACTIONS_SAMPLE_FILE)

    assert len(transactions) > 0


def test_transaction_status_values_are_expected():
    """
    Confirm that transaction_status only contains approved status values.
    """
    transactions = pd.read_csv(TRANSACTIONS_SAMPLE_FILE)

    expected_statuses = {
        "Completed",
        "Cancelled/Return",
        "Data Issue",
    }

    actual_statuses = set(transactions["transaction_status"].dropna().unique())

    unexpected_statuses = actual_statuses - expected_statuses

    assert not unexpected_statuses, f"Unexpected statuses: {unexpected_statuses}"


def test_completed_sales_amount_is_not_negative():
    """
    Completed sales amount should not be negative.

    Cancellation/return value is tracked separately in cancelled_amount.
    """
    transactions = pd.read_csv(TRANSACTIONS_SAMPLE_FILE)

    assert (transactions["completed_sales_amount"] >= 0).all()


def test_products_file_has_expected_columns():
    """
    Confirm that the product table has useful product-level fields.
    """
    products = pd.read_csv(PRODUCTS_FILE)

    expected_columns = {
        "stock_code",
        "product_description",
        "avg_unit_price",
        "transaction_line_count",
        "completed_line_count",
    }

    actual_columns = set(products.columns)

    missing_columns = expected_columns - actual_columns

    assert not missing_columns, f"Missing product columns: {missing_columns}"


def test_customers_file_has_expected_columns():
    """
    Confirm that the customer table has useful customer-level fields.
    """
    customers = pd.read_csv(CUSTOMERS_FILE)

    expected_columns = {
        "customer_id",
        "country",
        "first_invoice_date",
        "last_invoice_date",
        "transaction_line_count",
        "completed_sales_amount",
        "cancelled_amount",
    }

    actual_columns = set(customers.columns)

    missing_columns = expected_columns - actual_columns

    assert not missing_columns, f"Missing customer columns: {missing_columns}"


def test_executive_kpi_file_has_one_row():
    """
    Confirm that the executive KPI summary is a one-row summary file.
    """
    executive_kpi = pd.read_csv(EXECUTIVE_KPI_FILE)

    assert len(executive_kpi) == 1