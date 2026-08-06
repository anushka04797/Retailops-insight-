from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SUPPORT_DATA_DIR = PROJECT_ROOT / "data" / "support"
SQL_OUTPUT_DIR = PROJECT_ROOT / "reports" / "sql_outputs"
SUPPORT_REPORT_DIR = PROJECT_ROOT / "reports" / "support"

SUPPORT_TICKETS_FILE = SUPPORT_DATA_DIR / "reporting_support_tickets.csv"

RPT001_RECONCILIATION_FILE = SQL_OUTPUT_DIR / "rpt001_revenue_reconciliation.csv"
RPT002_CUSTOMER_IMPACT_FILE = SQL_OUTPUT_DIR / "rpt002_customer_id_impact.csv"
RPT003_DUPLICATE_IMPACT_FILE = SQL_OUTPUT_DIR / "rpt003_duplicate_row_impact.csv"

PRIORITY_SUMMARY_FILE = SUPPORT_REPORT_DIR / "support_ticket_priority_summary.csv"
CATEGORY_SUMMARY_FILE = SUPPORT_REPORT_DIR / "support_ticket_category_summary.csv"
INVESTIGATION_FINDINGS_FILE = SUPPORT_REPORT_DIR / "support_investigation_findings.csv"


def check_required_files() -> None:
    """
    Confirm that all required support and investigation files exist.
    """
    required_files = [
        SUPPORT_TICKETS_FILE,
        RPT001_RECONCILIATION_FILE,
        RPT002_CUSTOMER_IMPACT_FILE,
        RPT003_DUPLICATE_IMPACT_FILE,
    ]

    missing_files = [file for file in required_files if not file.exists()]

    if missing_files:
        missing_list = "\n".join(str(file) for file in missing_files)
        raise FileNotFoundError(
            f"Missing required files:\n{missing_list}"
        )


def load_support_files() -> dict[str, pd.DataFrame]:
    """
    Load support ticket and investigation output files.
    """
    return {
        "tickets": pd.read_csv(SUPPORT_TICKETS_FILE),
        "rpt001": pd.read_csv(RPT001_RECONCILIATION_FILE),
        "rpt002": pd.read_csv(RPT002_CUSTOMER_IMPACT_FILE),
        "rpt003": pd.read_csv(RPT003_DUPLICATE_IMPACT_FILE),
    }


def create_priority_summary(tickets: pd.DataFrame) -> pd.DataFrame:
    """
    Summarize support tickets by priority.
    """
    priority_summary = (
        tickets
        .groupby("priority")
        .agg(
            ticket_count=("ticket_id", "count"),
            affected_reports=("affected_report", "nunique"),
        )
        .reset_index()
        .sort_values(by="ticket_count", ascending=False)
    )

    return priority_summary


def create_category_summary(tickets: pd.DataFrame) -> pd.DataFrame:
    """
    Summarize support tickets by category.
    """
    category_summary = (
        tickets
        .groupby("category")
        .agg(
            ticket_count=("ticket_id", "count"),
            high_priority_count=(
                "priority",
                lambda values: (values == "High").sum()
            ),
            affected_reports=("affected_report", "nunique"),
        )
        .reset_index()
        .sort_values(by=["ticket_count", "high_priority_count"], ascending=False)
    )

    return category_summary


def create_investigation_findings(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Create a concise dashboard/report-ready investigation findings table.
    """
    tickets = data["tickets"]
    rpt001 = data["rpt001"].iloc[0]
    rpt002 = data["rpt002"].iloc[0]
    rpt003 = data["rpt003"].iloc[0]

    findings = [
        {
            "ticket_id": "RPT-001",
            "issue_type": "Revenue mismatch",
            "investigation_result": rpt001["investigation_result"],
            "key_metric": "net_sales_after_cancellations",
            "evidence": (
                f"Completed sales {rpt001['total_completed_sales_amount']:,.2f} "
                f"minus cancelled amount {rpt001['total_cancelled_amount']:,.2f} "
                f"equals recalculated net sales {rpt001['recalculated_net_sales']:,.2f}."
            ),
            "recommended_action": "Clarify completed sales, cancelled amount, and net sales KPI definitions.",
        },
        {
            "ticket_id": "RPT-002",
            "issue_type": "Missing customer IDs",
            "investigation_result": "Customer-level reporting is affected by missing CustomerID values.",
            "key_metric": "missing_customer_id_rate_percent",
            "evidence": (
                f"{rpt002['missing_customer_id_rows']:,.0f} transaction rows "
                f"have missing CustomerID values, representing "
                f"{rpt002['missing_customer_id_rate_percent']:.2f}% of transaction rows."
            ),
            "recommended_action": "Separate known and missing customer ID rows in customer-level reports.",
        },
        {
            "ticket_id": "RPT-003",
            "issue_type": "Duplicate row risk",
            "investigation_result": "Duplicate-flagged rows exist and should be monitored.",
            "key_metric": "duplicate_row_summary",
            "evidence": (
                f"{rpt003['row_count']:,.0f} duplicate-flagged rows were found, "
                f"with {rpt003['completed_sales_amount']:,.2f} in completed sales amount."
            ),
            "recommended_action": "Keep duplicate row monitoring visible in data quality reports.",
        },
    ]

    findings_df = pd.DataFrame(findings)

    ticket_details = tickets[[
        "ticket_id",
        "priority",
        "affected_report",
        "current_status",
        "business_impact",
    ]]

    findings_df = findings_df.merge(
        ticket_details,
        on="ticket_id",
        how="left",
    )

    return findings_df


def save_outputs(
    priority_summary: pd.DataFrame,
    category_summary: pd.DataFrame,
    investigation_findings: pd.DataFrame,
) -> None:
    """
    Save support summary outputs.
    """
    SUPPORT_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    priority_summary.to_csv(PRIORITY_SUMMARY_FILE, index=False)
    category_summary.to_csv(CATEGORY_SUMMARY_FILE, index=False)
    investigation_findings.to_csv(INVESTIGATION_FINDINGS_FILE, index=False)

    print(f"Saved priority summary: {PRIORITY_SUMMARY_FILE}")
    print(f"Saved category summary: {CATEGORY_SUMMARY_FILE}")
    print(f"Saved investigation findings: {INVESTIGATION_FINDINGS_FILE}")


def main() -> None:
    """
    Create support investigation summary outputs.
    """
    print("Creating support investigation summary outputs...")

    check_required_files()

    data = load_support_files()
    tickets = data["tickets"]

    priority_summary = create_priority_summary(tickets)
    category_summary = create_category_summary(tickets)
    investigation_findings = create_investigation_findings(data)

    save_outputs(
        priority_summary=priority_summary,
        category_summary=category_summary,
        investigation_findings=investigation_findings,
    )

    print("\nPriority summary:")
    print(priority_summary.to_string(index=False))

    print("\nCategory summary:")
    print(category_summary.to_string(index=False))

    print("\nInvestigation findings preview:")
    print(investigation_findings[[
        "ticket_id",
        "issue_type",
        "priority",
        "current_status",
        "recommended_action",
    ]].to_string(index=False))

    print("\nSupport investigation summary outputs created successfully.")


if __name__ == "__main__":
    main()