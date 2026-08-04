from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SQL_OUTPUT_DIR = PROJECT_ROOT / "reports" / "sql_outputs"
SUPPORT_DIR = PROJECT_ROOT / "data" / "support"

EXECUTIVE_KPI_FILE = SQL_OUTPUT_DIR / "executive_kpi_summary.csv"
DATA_QUALITY_KPI_FILE = SQL_OUTPUT_DIR / "data_quality_kpi_summary.csv"
TRANSACTION_STATUS_FILE = SQL_OUTPUT_DIR / "transaction_status_summary.csv"
CUSTOMER_COVERAGE_FILE = SQL_OUTPUT_DIR / "customer_id_coverage.csv"

SUPPORT_TICKETS_FILE = SUPPORT_DIR / "reporting_support_tickets.csv"


def load_metric_files() -> dict[str, pd.DataFrame]:
    """
    Load SQL-generated KPI and data quality output files.

    These files provide real project metrics that will be referenced
    in the synthetic support tickets.
    """
    required_files = [
        EXECUTIVE_KPI_FILE,
        DATA_QUALITY_KPI_FILE,
        TRANSACTION_STATUS_FILE,
        CUSTOMER_COVERAGE_FILE,
    ]

    missing_files = [file for file in required_files if not file.exists()]

    if missing_files:
        missing_list = "\n".join(str(file) for file in missing_files)
        raise FileNotFoundError(
            f"Missing required metric files:\n{missing_list}"
        )

    return {
        "executive_kpi": pd.read_csv(EXECUTIVE_KPI_FILE),
        "data_quality_kpi": pd.read_csv(DATA_QUALITY_KPI_FILE),
        "transaction_status": pd.read_csv(TRANSACTION_STATUS_FILE),
        "customer_coverage": pd.read_csv(CUSTOMER_COVERAGE_FILE),
    }


def build_support_tickets(metric_data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Build a synthetic support ticket log.

    The tickets are based on realistic reporting, data quality, and
    dashboard support scenarios connected to the project.
    """
    executive_kpi = metric_data["executive_kpi"].iloc[0]
    data_quality_kpi = metric_data["data_quality_kpi"].iloc[0]

    completed_sales = executive_kpi["total_completed_sales_amount"]
    cancelled_amount = executive_kpi["total_cancelled_amount"]
    net_sales = executive_kpi["net_sales_after_cancellations"]
    missing_customer_rate = executive_kpi["missing_customer_id_rate_percent"]
    duplicate_rate = executive_kpi["duplicate_row_rate_percent"]

    missing_customer_rows = data_quality_kpi["missing_customer_id_rows"]
    duplicate_rows = data_quality_kpi["duplicate_rows"]
    zero_or_negative_price_rows = data_quality_kpi["zero_or_negative_unit_price_rows"]
    data_quality_issue_records = data_quality_kpi["data_quality_issue_records"]

    tickets = [
        {
            "ticket_id": "RPT-001",
            "created_date": "2026-07-26",
            "reported_by": "Sales Operations Manager",
            "category": "Reporting Mismatch",
            "priority": "High",
            "affected_report": "Executive Sales KPI Summary",
            "issue_summary": "Dashboard net sales does not match the completed sales figure shown in the monthly report.",
            "reported_symptom": "User expected completed sales and net sales to be the same.",
            "suspected_area": "KPI definition / cancellation logic",
            "linked_metric": "net_sales_after_cancellations",
            "expected_value": round(completed_sales, 2),
            "observed_value": round(net_sales, 2),
            "root_cause_hypothesis": "The dashboard is subtracting cancellation/return amount while the user is comparing it against completed sales.",
            "current_status": "Investigated",
            "business_impact": "May cause confusion during sales performance review if KPI definitions are not clearly documented.",
        },
        {
            "ticket_id": "RPT-002",
            "created_date": "2026-07-26",
            "reported_by": "Customer Insights Analyst",
            "category": "Data Quality",
            "priority": "High",
            "affected_report": "Customer Sales Segmentation",
            "issue_summary": "Customer-level sales report is missing a large number of transaction rows.",
            "reported_symptom": "Customer segmentation totals are lower than overall completed sales totals.",
            "suspected_area": "Missing CustomerID values",
            "linked_metric": "missing_customer_id_rate_percent",
            "expected_value": "Customer IDs available for all transaction rows",
            "observed_value": f"{missing_customer_rows:,.0f} rows missing CustomerID; {missing_customer_rate:.2f}% missing rate",
            "root_cause_hypothesis": "A significant portion of transaction rows has missing customer IDs and cannot be assigned to known customers.",
            "current_status": "Investigated",
            "business_impact": "Customer-level analysis may be incomplete unless missing-customer rows are reported separately.",
        },
        {
            "ticket_id": "RPT-003",
            "created_date": "2026-07-27",
            "reported_by": "BI Dashboard User",
            "category": "Dashboard Data Trust",
            "priority": "Medium",
            "affected_report": "Product Sales Dashboard",
            "issue_summary": "Some transaction lines appear duplicated in reporting extracts.",
            "reported_symptom": "User noticed repeated invoice/product combinations in the export.",
            "suspected_area": "Duplicate transaction rows",
            "linked_metric": "duplicate_row_rate_percent",
            "expected_value": "No duplicate transaction rows",
            "observed_value": f"{duplicate_rows:,.0f} duplicate-flagged rows; {duplicate_rate:.2f}% duplicate row rate",
            "root_cause_hypothesis": "Duplicate rows exist in the source extract and should be flagged before reporting.",
            "current_status": "Investigated",
            "business_impact": "Duplicate rows may inflate transaction counts and should be monitored in data quality reporting.",
        },
        {
            "ticket_id": "RPT-004",
            "created_date": "2026-07-27",
            "reported_by": "Finance Reviewer",
            "category": "Revenue Logic",
            "priority": "High",
            "affected_report": "Revenue Summary",
            "issue_summary": "Cancelled/return values need to be explained separately from completed sales.",
            "reported_symptom": "Cancelled amount appears as a separate KPI but users are unsure how it affects net sales.",
            "suspected_area": "Cancellation/return reporting logic",
            "linked_metric": "total_cancelled_amount",
            "expected_value": "Clear separation between completed sales and cancelled amount",
            "observed_value": round(cancelled_amount, 2),
            "root_cause_hypothesis": "Cancelled/return rows are correctly separated, but dashboard users need KPI definitions.",
            "current_status": "Investigated",
            "business_impact": "Unclear cancellation logic can lead to incorrect interpretation of sales performance.",
        },
        {
            "ticket_id": "RPT-005",
            "created_date": "2026-07-28",
            "reported_by": "Data Quality Reviewer",
            "category": "Invalid Pricing",
            "priority": "Medium",
            "affected_report": "Data Quality Monitor",
            "issue_summary": "Rows with zero or negative unit price were found during validation.",
            "reported_symptom": "Some rows cannot be used safely for revenue reporting.",
            "suspected_area": "UnitPrice source data quality",
            "linked_metric": "zero_or_negative_unit_price_rows",
            "expected_value": "Unit price greater than zero for sales reporting rows",
            "observed_value": f"{zero_or_negative_price_rows:,.0f} rows with zero or negative unit price",
            "root_cause_hypothesis": "Some source rows contain invalid pricing values and should be classified as data issues.",
            "current_status": "Investigated",
            "business_impact": "Invalid pricing rows should be excluded from completed sales KPIs.",
        },
        {
            "ticket_id": "RPT-006",
            "created_date": "2026-07-28",
            "reported_by": "Reporting Support Queue",
            "category": "Data Quality Monitoring",
            "priority": "Medium",
            "affected_report": "Data Quality Issue Log",
            "issue_summary": "Data quality issue log contains many issue records and needs summary reporting.",
            "reported_symptom": "Users need a simple count of major issue types instead of row-level issue exports.",
            "suspected_area": "Data quality issue reporting",
            "linked_metric": "data_quality_issue_records",
            "expected_value": "Summarized issue categories available",
            "observed_value": f"{data_quality_issue_records:,.0f} row-level issue records",
            "root_cause_hypothesis": "The issue log is detailed and should be paired with summary views for business users.",
            "current_status": "Investigated",
            "business_impact": "Without summary views, data quality logs may be too detailed for quick decision-making.",
        },
    ]

    return pd.DataFrame(tickets)


def save_support_tickets(tickets: pd.DataFrame) -> None:
    """
    Save the support ticket dataset.
    """
    SUPPORT_DIR.mkdir(parents=True, exist_ok=True)

    tickets.to_csv(SUPPORT_TICKETS_FILE, index=False)

    print(f"Saved support tickets: {SUPPORT_TICKETS_FILE}")
    print(f"Support ticket count: {len(tickets)}")


def main() -> None:
    """
    Create the synthetic reporting support ticket dataset.
    """
    print("Creating reporting support tickets...")

    metric_data = load_metric_files()
    tickets = build_support_tickets(metric_data)
    save_support_tickets(tickets)

    print("\nSupport ticket preview:")
    print(tickets[[
        "ticket_id",
        "category",
        "priority",
        "affected_report",
        "current_status",
    ]].to_string(index=False))

    print("\nSupport ticket generation completed successfully.")


if __name__ == "__main__":
    main()