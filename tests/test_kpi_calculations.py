import pandas as pd

from src.kpi_calculations import (
    calculate_total_completed_sales,
    calculate_total_cancelled_amount,
    calculate_net_sales_after_cancellations,
    calculate_completed_invoice_count,
    calculate_average_order_value,
    calculate_cancellation_amount_rate_percent,
    calculate_missing_customer_id_rate_percent,
    calculate_duplicate_row_rate_percent,
    build_executive_kpi_summary,
)


def create_sample_transactions() -> pd.DataFrame:
    """
    Create a small controlled transaction dataset for testing.

    This fake dataset is intentionally small so we can calculate expected
    results by hand.
    """
    return pd.DataFrame({
        "invoice_no": ["1001", "1001", "1002", "C1003", "1004"],
        "transaction_status": [
            "Completed",
            "Completed",
            "Completed",
            "Cancelled/Return",
            "Data Issue",
        ],
        "completed_sales_amount": [100.00, 50.00, 200.00, 0.00, 0.00],
        "cancelled_amount": [0.00, 0.00, 0.00, 75.00, 0.00],
        "customer_id": ["12345", "12345", "UNKNOWN", "45678", "UNKNOWN"],
        "is_duplicate_row": [0, 0, 1, 0, 0],
    })


def test_total_completed_sales():
    transactions = create_sample_transactions()

    result = calculate_total_completed_sales(transactions)

    assert result == 350.00


def test_total_cancelled_amount():
    transactions = create_sample_transactions()

    result = calculate_total_cancelled_amount(transactions)

    assert result == 75.00


def test_net_sales_after_cancellations():
    transactions = create_sample_transactions()

    result = calculate_net_sales_after_cancellations(transactions)

    assert result == 275.00


def test_completed_invoice_count():
    transactions = create_sample_transactions()

    result = calculate_completed_invoice_count(transactions)

    assert result == 2


def test_average_order_value():
    transactions = create_sample_transactions()

    result = calculate_average_order_value(transactions)

    assert result == 175.00


def test_cancellation_amount_rate_percent():
    transactions = create_sample_transactions()

    result = calculate_cancellation_amount_rate_percent(transactions)

    assert result == 17.65


def test_missing_customer_id_rate_percent():
    transactions = create_sample_transactions()

    result = calculate_missing_customer_id_rate_percent(transactions)

    assert result == 40.00


def test_duplicate_row_rate_percent():
    transactions = create_sample_transactions()

    result = calculate_duplicate_row_rate_percent(transactions)

    assert result == 20.00


def test_build_executive_kpi_summary():
    transactions = create_sample_transactions()

    result = build_executive_kpi_summary(transactions)

    assert result["total_transaction_lines"] == 5
    assert result["completed_transaction_lines"] == 3
    assert result["cancelled_return_lines"] == 1
    assert result["data_issue_lines"] == 1
    assert result["completed_invoice_count"] == 2
    assert result["total_completed_sales_amount"] == 350.00
    assert result["total_cancelled_amount"] == 75.00
    assert result["net_sales_after_cancellations"] == 275.00
    assert result["average_order_value"] == 175.00
    assert result["cancellation_amount_rate_percent"] == 17.65
    assert result["missing_customer_id_rows"] == 2
    assert result["missing_customer_id_rate_percent"] == 40.00
    assert result["duplicate_rows"] == 1
    assert result["duplicate_row_rate_percent"] == 20.00