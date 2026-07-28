import pandas as pd


def calculate_total_completed_sales(transactions: pd.DataFrame) -> float:
    """
    Calculate total completed sales amount.

    This uses completed_sales_amount instead of raw line_revenue because
    completed_sales_amount excludes cancellations, returns, and data issue rows.
    """
    return round(transactions["completed_sales_amount"].sum(), 2)


def calculate_total_cancelled_amount(transactions: pd.DataFrame) -> float:
    """
    Calculate total cancelled/return amount.

    cancelled_amount is stored as a positive value so it can be reported clearly.
    """
    return round(transactions["cancelled_amount"].sum(), 2)


def calculate_net_sales_after_cancellations(transactions: pd.DataFrame) -> float:
    """
    Calculate simplified net sales after cancellations.

    Formula:
    completed sales amount - cancelled amount
    """
    completed_sales = calculate_total_completed_sales(transactions)
    cancelled_amount = calculate_total_cancelled_amount(transactions)

    return round(completed_sales - cancelled_amount, 2)


def calculate_completed_invoice_count(transactions: pd.DataFrame) -> int:
    """
    Count unique invoices that contain completed transaction rows.
    """
    completed_transactions = transactions[
        transactions["transaction_status"] == "Completed"
    ]

    return int(completed_transactions["invoice_no"].nunique())


def calculate_average_order_value(transactions: pd.DataFrame) -> float:
    """
    Calculate average order value.

    Formula:
    completed sales amount / completed invoice count

    If there are no completed invoices, return 0.0.
    """
    completed_sales = calculate_total_completed_sales(transactions)
    completed_invoice_count = calculate_completed_invoice_count(transactions)

    if completed_invoice_count == 0:
        return 0.0

    return round(completed_sales / completed_invoice_count, 2)


def calculate_cancellation_amount_rate_percent(transactions: pd.DataFrame) -> float:
    """
    Calculate cancellation amount rate as a percentage.

    Formula:
    cancelled amount / (completed sales amount + cancelled amount) * 100

    If there is no sales or cancellation amount, return 0.0.
    """
    completed_sales = calculate_total_completed_sales(transactions)
    cancelled_amount = calculate_total_cancelled_amount(transactions)

    denominator = completed_sales + cancelled_amount

    if denominator == 0:
        return 0.0

    return round(cancelled_amount / denominator * 100, 2)


def calculate_missing_customer_id_rate_percent(transactions: pd.DataFrame) -> float:
    """
    Calculate percentage of rows with missing customer IDs.

    Missing customer IDs are standardized as UNKNOWN.
    """
    if len(transactions) == 0:
        return 0.0

    missing_customer_rows = (transactions["customer_id"] == "UNKNOWN").sum()

    return round(missing_customer_rows / len(transactions) * 100, 2)


def calculate_duplicate_row_rate_percent(transactions: pd.DataFrame) -> float:
    """
    Calculate percentage of rows flagged as duplicates.
    """
    if len(transactions) == 0:
        return 0.0

    duplicate_rows = transactions["is_duplicate_row"].sum()

    return round(duplicate_rows / len(transactions) * 100, 2)


def build_executive_kpi_summary(transactions: pd.DataFrame) -> dict:
    """
    Build a dictionary of core executive KPIs.

    This function mirrors the KPI logic used in SQL, but keeps the calculation
    reusable from Python.
    """
    total_transaction_lines = len(transactions)

    completed_transaction_lines = int(
        (transactions["transaction_status"] == "Completed").sum()
    )

    cancelled_return_lines = int(
        (transactions["transaction_status"] == "Cancelled/Return").sum()
    )

    data_issue_lines = int(
        (transactions["transaction_status"] == "Data Issue").sum()
    )

    missing_customer_id_rows = int(
        (transactions["customer_id"] == "UNKNOWN").sum()
    )

    duplicate_rows = int(
        transactions["is_duplicate_row"].sum()
    )

    return {
        "total_transaction_lines": total_transaction_lines,
        "completed_transaction_lines": completed_transaction_lines,
        "cancelled_return_lines": cancelled_return_lines,
        "data_issue_lines": data_issue_lines,
        "completed_invoice_count": calculate_completed_invoice_count(transactions),
        "total_completed_sales_amount": calculate_total_completed_sales(transactions),
        "total_cancelled_amount": calculate_total_cancelled_amount(transactions),
        "net_sales_after_cancellations": calculate_net_sales_after_cancellations(transactions),
        "average_order_value": calculate_average_order_value(transactions),
        "cancellation_amount_rate_percent": calculate_cancellation_amount_rate_percent(transactions),
        "missing_customer_id_rows": missing_customer_id_rows,
        "missing_customer_id_rate_percent": calculate_missing_customer_id_rate_percent(transactions),
        "duplicate_rows": duplicate_rows,
        "duplicate_row_rate_percent": calculate_duplicate_row_rate_percent(transactions),
    }