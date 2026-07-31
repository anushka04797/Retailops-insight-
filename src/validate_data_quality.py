from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"
REPORT_DIR = PROJECT_ROOT / "reports" / "data_quality"
SQL_OUTPUT_DIR = PROJECT_ROOT / "reports" / "sql_outputs"

FULL_TRANSACTIONS_FILE = CLEANED_DIR / "online_retail_transactions_cleaned.csv"
SAMPLE_TRANSACTIONS_FILE = CLEANED_DIR / "online_retail_transactions_cleaned_sample.csv"

PRODUCTS_FILE = CLEANED_DIR / "products_cleaned.csv"
CUSTOMERS_FILE = CLEANED_DIR / "customers_cleaned.csv"

FULL_DATA_QUALITY_ISSUES_FILE = REPORT_DIR / "data_quality_issues.csv"
SAMPLE_DATA_QUALITY_ISSUES_FILE = REPORT_DIR / "data_quality_issues_sample.csv"
CLEANING_SUMMARY_FILE = REPORT_DIR / "cleaning_summary.csv"

EXECUTIVE_KPI_FILE = SQL_OUTPUT_DIR / "executive_kpi_summary.csv"

VALIDATION_RESULTS_FILE = REPORT_DIR / "validation_results.csv"
VALIDATION_SUMMARY_FILE = REPORT_DIR / "validation_summary.csv"


EXPECTED_TRANSACTION_COLUMNS = {
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
}

EXPECTED_TRANSACTION_STATUSES = {
    "Completed",
    "Cancelled/Return",
    "Data Issue",
}


def add_result(
    results: list[dict[str, Any]],
    validation_name: str,
    status: str,
    severity: str,
    expected: Any,
    actual: Any,
    notes: str,
) -> None:
    """
    Add one validation result to the results list.

    Status values:
    - PASS
    - WARN
    - FAIL
    - SKIP
    """
    results.append({
        "validation_name": validation_name,
        "status": status,
        "severity": severity,
        "expected": expected,
        "actual": actual,
        "notes": notes,
    })


def normalize_bool_series(series: pd.Series) -> pd.Series:
    """
    Convert common boolean-like values into actual True/False values.

    This handles values such as:
    - True / False
    - 1 / 0
    - "True" / "False"
    - "1" / "0"
    """
    return series.map({
        True: True,
        False: False,
        1: True,
        0: False,
        "True": True,
        "False": False,
        "true": True,
        "false": False,
        "1": True,
        "0": False,
    }).fillna(False)


def choose_transactions_file() -> tuple[Path, str]:
    """
    Choose which transaction file to validate.

    Preference:
    1. Full local cleaned transaction file
    2. GitHub-safe cleaned sample file

    The full file is used locally.
    The sample file is useful in environments where the full file is not available.
    """
    if FULL_TRANSACTIONS_FILE.exists():
        return FULL_TRANSACTIONS_FILE, "full"

    return SAMPLE_TRANSACTIONS_FILE, "sample"

def choose_data_quality_issues_file() -> tuple[Path, str]:
    """
    Choose which data quality issue file to validate.

    Preference:
    1. Full local data quality issue file
    2. GitHub-safe data quality issue sample file
    """
    if FULL_DATA_QUALITY_ISSUES_FILE.exists():
        return FULL_DATA_QUALITY_ISSUES_FILE, "full"

    return SAMPLE_DATA_QUALITY_ISSUES_FILE, "sample"

def check_required_files(
    results: list[dict[str, Any]],
    transactions_file: Path,
    data_quality_issues_file: Path,
) -> None:
    """
    Validate that required project files exist.
    """
    required_files = [
        transactions_file,
        PRODUCTS_FILE,
        CUSTOMERS_FILE,
        data_quality_issues_file,
        CLEANING_SUMMARY_FILE,
        EXECUTIVE_KPI_FILE,
   ]

    for file_path in required_files:
        if file_path.exists():
            add_result(
                results,
                validation_name=f"Required file exists: {file_path.relative_to(PROJECT_ROOT)}",
                status="PASS",
                severity="critical",
                expected="file exists",
                actual="file exists",
                notes="Required file is available.",
            )
        else:
            add_result(
                results,
                validation_name=f"Required file exists: {file_path.relative_to(PROJECT_ROOT)}",
                status="FAIL",
                severity="critical",
                expected="file exists",
                actual="missing",
                notes="Required file is missing.",
            )


def load_data(
    transactions_file: Path,
    data_quality_issues_file: Path,
) -> dict[str, pd.DataFrame]:
    """
    Load the files required for validation.
    """
    data = {
        "transactions": pd.read_csv(transactions_file),
        "products": pd.read_csv(PRODUCTS_FILE),
        "customers": pd.read_csv(CUSTOMERS_FILE),
        "data_quality_issues": pd.read_csv(data_quality_issues_file),
        "cleaning_summary": pd.read_csv(CLEANING_SUMMARY_FILE),
        "executive_kpi": pd.read_csv(EXECUTIVE_KPI_FILE),
    }

    return data


def validate_transaction_schema(
    results: list[dict[str, Any]],
    transactions: pd.DataFrame,
) -> None:
    """
    Validate that the transaction table has the expected columns.
    """
    actual_columns = set(transactions.columns)
    missing_columns = EXPECTED_TRANSACTION_COLUMNS - actual_columns

    if not missing_columns:
        add_result(
            results,
            validation_name="Transaction table contains expected columns",
            status="PASS",
            severity="critical",
            expected=f"{len(EXPECTED_TRANSACTION_COLUMNS)} required columns",
            actual=f"{len(actual_columns)} columns found",
            notes="All required transaction columns are present.",
        )
    else:
        add_result(
            results,
            validation_name="Transaction table contains expected columns",
            status="FAIL",
            severity="critical",
            expected=sorted(EXPECTED_TRANSACTION_COLUMNS),
            actual=f"Missing columns: {sorted(missing_columns)}",
            notes="The transaction table is missing required reporting columns.",
        )


def validate_transaction_values(
    results: list[dict[str, Any]],
    transactions: pd.DataFrame,
) -> None:
    """
    Validate important transaction-level values.
    """
    invalid_statuses = (
        set(transactions["transaction_status"].dropna().unique())
        - EXPECTED_TRANSACTION_STATUSES
    )

    if not invalid_statuses:
        add_result(
            results,
            validation_name="Transaction status values are controlled",
            status="PASS",
            severity="critical",
            expected=sorted(EXPECTED_TRANSACTION_STATUSES),
            actual=sorted(transactions["transaction_status"].dropna().unique()),
            notes="All transaction status values are expected.",
        )
    else:
        add_result(
            results,
            validation_name="Transaction status values are controlled",
            status="FAIL",
            severity="critical",
            expected=sorted(EXPECTED_TRANSACTION_STATUSES),
            actual=sorted(invalid_statuses),
            notes="Unexpected transaction status values were found.",
        )

    raw_row_id_nulls = int(transactions["raw_row_id"].isna().sum())
    raw_row_id_duplicates = int(transactions["raw_row_id"].duplicated().sum())

    if raw_row_id_nulls == 0 and raw_row_id_duplicates == 0:
        add_result(
            results,
            validation_name="raw_row_id is complete and unique",
            status="PASS",
            severity="critical",
            expected="0 nulls and 0 duplicates",
            actual=f"{raw_row_id_nulls} nulls, {raw_row_id_duplicates} duplicates",
            notes="Each transaction row has a unique traceable raw row ID.",
        )
    else:
        add_result(
            results,
            validation_name="raw_row_id is complete and unique",
            status="FAIL",
            severity="critical",
            expected="0 nulls and 0 duplicates",
            actual=f"{raw_row_id_nulls} nulls, {raw_row_id_duplicates} duplicates",
            notes="raw_row_id should uniquely identify each cleaned row.",
        )


def validate_financial_logic(
    results: list[dict[str, Any]],
    transactions: pd.DataFrame,
) -> None:
    """
    Validate reporting amount fields.
    """
    calculated_line_revenue = transactions["quantity"] * transactions["unit_price"]

    line_revenue_mismatches = int(
        ((transactions["line_revenue"] - calculated_line_revenue).abs() > 0.01).sum()
    )

    if line_revenue_mismatches == 0:
        add_result(
            results,
            validation_name="line_revenue equals quantity multiplied by unit_price",
            status="PASS",
            severity="critical",
            expected="0 mismatches",
            actual=line_revenue_mismatches,
            notes="line_revenue calculation is consistent.",
        )
    else:
        add_result(
            results,
            validation_name="line_revenue equals quantity multiplied by unit_price",
            status="FAIL",
            severity="critical",
            expected="0 mismatches",
            actual=line_revenue_mismatches,
            notes="Some line_revenue values do not match quantity * unit_price.",
        )

    completed_rows = transactions["transaction_status"] == "Completed"
    non_completed_rows = ~completed_rows

    completed_amount_mismatches = int(
        (
            (
                transactions.loc[completed_rows, "completed_sales_amount"]
                - transactions.loc[completed_rows, "line_revenue"]
            ).abs() > 0.01
        ).sum()
    )

    non_completed_amount_mismatches = int(
        (transactions.loc[non_completed_rows, "completed_sales_amount"].abs() > 0.01).sum()
    )

    if completed_amount_mismatches == 0 and non_completed_amount_mismatches == 0:
        add_result(
            results,
            validation_name="completed_sales_amount follows transaction status logic",
            status="PASS",
            severity="critical",
            expected="completed rows equal line_revenue; non-completed rows equal 0",
            actual="0 mismatches",
            notes="completed_sales_amount is consistent with reporting logic.",
        )
    else:
        add_result(
            results,
            validation_name="completed_sales_amount follows transaction status logic",
            status="FAIL",
            severity="critical",
            expected="completed rows equal line_revenue; non-completed rows equal 0",
            actual=(
                f"{completed_amount_mismatches} completed mismatches; "
                f"{non_completed_amount_mismatches} non-completed mismatches"
            ),
            notes="completed_sales_amount does not fully match expected reporting logic.",
        )

    cancelled_rows = transactions["transaction_status"] == "Cancelled/Return"
    non_cancelled_rows = ~cancelled_rows

    cancelled_amount_mismatches = int(
        (
            (
                transactions.loc[cancelled_rows, "cancelled_amount"]
                - transactions.loc[cancelled_rows, "line_revenue"].abs()
            ).abs() > 0.01
        ).sum()
    )

    non_cancelled_amount_mismatches = int(
        (transactions.loc[non_cancelled_rows, "cancelled_amount"].abs() > 0.01).sum()
    )

    if cancelled_amount_mismatches == 0 and non_cancelled_amount_mismatches == 0:
        add_result(
            results,
            validation_name="cancelled_amount follows transaction status logic",
            status="PASS",
            severity="critical",
            expected="cancelled rows equal absolute line_revenue; non-cancelled rows equal 0",
            actual="0 mismatches",
            notes="cancelled_amount is consistent with reporting logic.",
        )
    else:
        add_result(
            results,
            validation_name="cancelled_amount follows transaction status logic",
            status="FAIL",
            severity="critical",
            expected="cancelled rows equal absolute line_revenue; non-cancelled rows equal 0",
            actual=(
                f"{cancelled_amount_mismatches} cancelled mismatches; "
                f"{non_cancelled_amount_mismatches} non-cancelled mismatches"
            ),
            notes="cancelled_amount does not fully match expected reporting logic.",
        )

    negative_completed_sales = int((transactions["completed_sales_amount"] < 0).sum())
    negative_cancelled_amount = int((transactions["cancelled_amount"] < 0).sum())

    if negative_completed_sales == 0 and negative_cancelled_amount == 0:
        add_result(
            results,
            validation_name="Reporting amount fields are non-negative",
            status="PASS",
            severity="critical",
            expected="0 negative reporting amounts",
            actual="0 negative reporting amounts",
            notes="completed_sales_amount and cancelled_amount are non-negative.",
        )
    else:
        add_result(
            results,
            validation_name="Reporting amount fields are non-negative",
            status="FAIL",
            severity="critical",
            expected="0 negative reporting amounts",
            actual=(
                f"{negative_completed_sales} negative completed_sales_amount rows; "
                f"{negative_cancelled_amount} negative cancelled_amount rows"
            ),
            notes="Reporting amount fields should not be negative.",
        )


def validate_flag_consistency(
    results: list[dict[str, Any]],
    transactions: pd.DataFrame,
) -> None:
    """
    Validate that important data quality flags match their underlying values.
    """
    missing_customer_flag = normalize_bool_series(transactions["is_missing_customer_id"])
    expected_missing_customer_flag = transactions["customer_id"] == "UNKNOWN"

    missing_customer_flag_mismatches = int(
        (missing_customer_flag != expected_missing_customer_flag).sum()
    )

    if missing_customer_flag_mismatches == 0:
        add_result(
            results,
            validation_name="is_missing_customer_id flag matches customer_id",
            status="PASS",
            severity="critical",
            expected="0 mismatches",
            actual=missing_customer_flag_mismatches,
            notes="Missing customer ID flag is consistent.",
        )
    else:
        add_result(
            results,
            validation_name="is_missing_customer_id flag matches customer_id",
            status="FAIL",
            severity="critical",
            expected="0 mismatches",
            actual=missing_customer_flag_mismatches,
            notes="Missing customer ID flag does not match customer_id values.",
        )

    missing_description_flag = normalize_bool_series(transactions["is_missing_description"])
    expected_missing_description_flag = transactions["description"] == "UNKNOWN_DESCRIPTION"

    missing_description_flag_mismatches = int(
        (missing_description_flag != expected_missing_description_flag).sum()
    )

    if missing_description_flag_mismatches == 0:
        add_result(
            results,
            validation_name="is_missing_description flag matches description",
            status="PASS",
            severity="major",
            expected="0 mismatches",
            actual=missing_description_flag_mismatches,
            notes="Missing description flag is consistent.",
        )
    else:
        add_result(
            results,
            validation_name="is_missing_description flag matches description",
            status="FAIL",
            severity="major",
            expected="0 mismatches",
            actual=missing_description_flag_mismatches,
            notes="Missing description flag does not match description values.",
        )


def validate_master_tables(
    results: list[dict[str, Any]],
    products: pd.DataFrame,
    customers: pd.DataFrame,
) -> None:
    """
    Validate product and customer master-style tables.
    """
    product_duplicate_count = int(products["stock_code"].duplicated().sum())

    if product_duplicate_count == 0:
        add_result(
            results,
            validation_name="Product table has unique stock_code values",
            status="PASS",
            severity="major",
            expected="0 duplicate stock_code values",
            actual=product_duplicate_count,
            notes="Product table has one row per stock code.",
        )
    else:
        add_result(
            results,
            validation_name="Product table has unique stock_code values",
            status="FAIL",
            severity="major",
            expected="0 duplicate stock_code values",
            actual=product_duplicate_count,
            notes="Product table should have unique stock_code values.",
        )

    customer_duplicate_count = int(customers["customer_id"].duplicated().sum())

    if customer_duplicate_count == 0:
        add_result(
            results,
            validation_name="Customer table has unique customer_id values",
            status="PASS",
            severity="major",
            expected="0 duplicate customer_id values",
            actual=customer_duplicate_count,
            notes="Customer table has one row per known customer ID.",
        )
    else:
        add_result(
            results,
            validation_name="Customer table has unique customer_id values",
            status="FAIL",
            severity="major",
            expected="0 duplicate customer_id values",
            actual=customer_duplicate_count,
            notes="Customer table should have unique customer_id values.",
        )


def get_summary_value(cleaning_summary: pd.DataFrame, metric: str) -> float:
    """
    Get one numeric value from cleaning_summary.csv.
    """
    value = cleaning_summary.loc[
        cleaning_summary["metric"] == metric,
        "value",
    ].iloc[0]

    return float(value)


def compare_number(
    results: list[dict[str, Any]],
    validation_name: str,
    expected: float,
    actual: float,
    severity: str = "major",
    tolerance: float = 0.01,
) -> None:
    """
    Compare two numeric values and add a validation result.
    """
    difference = abs(expected - actual)

    if difference <= tolerance:
        add_result(
            results,
            validation_name=validation_name,
            status="PASS",
            severity=severity,
            expected=round(expected, 2),
            actual=round(actual, 2),
            notes="Value matches expected result.",
        )
    else:
        add_result(
            results,
            validation_name=validation_name,
            status="FAIL",
            severity=severity,
            expected=round(expected, 2),
            actual=round(actual, 2),
            notes=f"Value mismatch. Difference: {round(difference, 2)}",
        )


def validate_cleaning_summary_consistency(
    results: list[dict[str, Any]],
    transactions: pd.DataFrame,
    data_quality_issues: pd.DataFrame,
    cleaning_summary: pd.DataFrame,
    transaction_scope: str,
) -> None:
    """
    Validate that cleaning_summary.csv matches the full transaction dataset.

    This is only meaningful when the full transaction file is available.
    """
    if transaction_scope != "full":
        add_result(
            results,
            validation_name="Cleaning summary consistency check",
            status="SKIP",
            severity="major",
            expected="full transaction file available",
            actual="sample transaction file used",
            notes="Skipped because only the sample transaction file is available.",
        )
        return

    duplicate_flag = normalize_bool_series(transactions["is_duplicate_row"])
    zero_or_negative_price_flag = normalize_bool_series(
        transactions["is_zero_or_negative_unit_price"]
    )

    summary_comparisons = {
        "raw_rows": len(transactions),
        "cleaned_transaction_rows": len(transactions),
        "completed_rows": int((transactions["transaction_status"] == "Completed").sum()),
        "cancelled_return_rows": int((transactions["transaction_status"] == "Cancelled/Return").sum()),
        "data_issue_rows": int((transactions["transaction_status"] == "Data Issue").sum()),
        "missing_customer_id_rows": int((transactions["customer_id"] == "UNKNOWN").sum()),
        "duplicate_rows": int(duplicate_flag.sum()),
        "zero_or_negative_unit_price_rows": int(zero_or_negative_price_flag.sum()),
        "unique_invoice_count": int(transactions["invoice_no"].nunique()),
        "unique_product_count": int(transactions["stock_code"].nunique()),
        "known_customer_count": int(
            transactions.loc[transactions["customer_id"] != "UNKNOWN", "customer_id"].nunique()
        ),
        "country_count": int(transactions["country"].nunique()),
        "data_quality_issue_records": len(data_quality_issues),
        "total_completed_sales_amount": round(transactions["completed_sales_amount"].sum(), 2),
        "total_cancelled_amount": round(transactions["cancelled_amount"].sum(), 2),
    }

    for metric, actual_value in summary_comparisons.items():
        expected_value = get_summary_value(cleaning_summary, metric)

        compare_number(
            results,
            validation_name=f"Cleaning summary matches actual data: {metric}",
            expected=expected_value,
            actual=actual_value,
            severity="major",
            tolerance=0.01,
        )


def validate_executive_kpi_consistency(
    results: list[dict[str, Any]],
    transactions: pd.DataFrame,
    executive_kpi: pd.DataFrame,
    transaction_scope: str,
) -> None:
    """
    Validate that executive_kpi_summary.csv matches the full transaction dataset.

    This is only meaningful when the full transaction file is available.
    """
    if transaction_scope != "full":
        add_result(
            results,
            validation_name="Executive KPI consistency check",
            status="SKIP",
            severity="major",
            expected="full transaction file available",
            actual="sample transaction file used",
            notes="Skipped because only the sample transaction file is available.",
        )
        return

    kpi_row = executive_kpi.iloc[0]

    duplicate_flag = normalize_bool_series(transactions["is_duplicate_row"])

    completed_invoice_count = int(
        transactions.loc[
            transactions["transaction_status"] == "Completed",
            "invoice_no",
        ].nunique()
    )

    total_completed_sales = round(transactions["completed_sales_amount"].sum(), 2)
    total_cancelled_amount = round(transactions["cancelled_amount"].sum(), 2)
    total_transaction_lines = len(transactions)
    missing_customer_rows = int((transactions["customer_id"] == "UNKNOWN").sum())
    duplicate_rows = int(duplicate_flag.sum())

    calculated_kpis = {
        "total_transaction_lines": total_transaction_lines,
        "completed_transaction_lines": int(
            (transactions["transaction_status"] == "Completed").sum()
        ),
        "cancelled_return_lines": int(
            (transactions["transaction_status"] == "Cancelled/Return").sum()
        ),
        "data_issue_lines": int(
            (transactions["transaction_status"] == "Data Issue").sum()
        ),
        "completed_invoice_count": completed_invoice_count,
        "total_completed_sales_amount": total_completed_sales,
        "total_cancelled_amount": total_cancelled_amount,
        "net_sales_after_cancellations": round(
            total_completed_sales - total_cancelled_amount,
            2,
        ),
        "average_order_value": round(
            total_completed_sales / completed_invoice_count,
            2,
        ),
        "average_completed_line_value": round(
            total_completed_sales
            / int((transactions["transaction_status"] == "Completed").sum()),
            2,
        ),
        "cancellation_amount_rate_percent": round(
            total_cancelled_amount
            / (total_completed_sales + total_cancelled_amount)
            * 100,
            2,
        ),
        "unique_product_count": int(transactions["stock_code"].nunique()),
        "known_customer_count": int(
            transactions.loc[transactions["customer_id"] != "UNKNOWN", "customer_id"].nunique()
        ),
        "country_count": int(transactions["country"].nunique()),
        "missing_customer_id_rows": missing_customer_rows,
        "missing_customer_id_rate_percent": round(
            missing_customer_rows * 100.0 / total_transaction_lines,
            2,
        ),
        "duplicate_rows": duplicate_rows,
        "duplicate_row_rate_percent": round(
            duplicate_rows * 100.0 / total_transaction_lines,
            2,
        ),
    }

    for metric, actual_value in calculated_kpis.items():
        expected_value = float(kpi_row[metric])

        compare_number(
            results,
            validation_name=f"Executive KPI matches actual data: {metric}",
            expected=expected_value,
            actual=actual_value,
            severity="major",
            tolerance=0.01,
        )


def save_validation_outputs(results: list[dict[str, Any]]) -> pd.DataFrame:
    """
    Save validation results and summary files.
    """
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    results_df = pd.DataFrame(results)
    results_df.to_csv(VALIDATION_RESULTS_FILE, index=False)

    summary_df = (
        results_df
        .groupby(["status", "severity"])
        .size()
        .reset_index(name="validation_count")
        .sort_values(["status", "severity"])
    )

    summary_df.to_csv(VALIDATION_SUMMARY_FILE, index=False)

    print("\n=== Validation Summary ===")
    print(summary_df.to_string(index=False))

    print(f"\nSaved validation results: {VALIDATION_RESULTS_FILE}")
    print(f"Saved validation summary: {VALIDATION_SUMMARY_FILE}")

    return results_df


def main() -> None:
    """
    Run the full data quality validation workflow.
    """
    print("Starting data quality validation...")

    results: list[dict[str, Any]] = []

    transactions_file, transaction_scope = choose_transactions_file()
    data_quality_issues_file, issue_log_scope = choose_data_quality_issues_file()

    print(f"Transaction file selected: {transactions_file}")
    print(f"Transaction validation scope: {transaction_scope}")
    print(f"Data quality issue file selected: {data_quality_issues_file}")
    print(f"Data quality issue validation scope: {issue_log_scope}")

    check_required_files(
        results,
        transactions_file,
        data_quality_issues_file,
    )

    has_critical_missing_file = any(
        result["status"] == "FAIL" and result["severity"] == "critical"
        for result in results
    )

    if has_critical_missing_file:
        save_validation_outputs(results)
        raise SystemExit("Validation failed because one or more critical files are missing.")

    data = load_data(
    transactions_file,
    data_quality_issues_file,)

    transactions = data["transactions"]
    products = data["products"]
    customers = data["customers"]
    data_quality_issues = data["data_quality_issues"]
    cleaning_summary = data["cleaning_summary"]
    executive_kpi = data["executive_kpi"]

    print(f"\nTransactions rows loaded for validation: {len(transactions):,}")
    print(f"Products rows loaded for validation: {len(products):,}")
    print(f"Customers rows loaded for validation: {len(customers):,}")
    print(f"Data quality issue rows loaded for validation: {len(data_quality_issues):,}")

    validate_transaction_schema(results, transactions)
    validate_transaction_values(results, transactions)
    validate_financial_logic(results, transactions)
    validate_flag_consistency(results, transactions)
    validate_master_tables(results, products, customers)
    validate_cleaning_summary_consistency(
        results,
        transactions,
        data_quality_issues,
        cleaning_summary,
        transaction_scope,
    )
    validate_executive_kpi_consistency(
        results,
        transactions,
        executive_kpi,
        transaction_scope,
    )

    results_df = save_validation_outputs(results)

    fail_count = int((results_df["status"] == "FAIL").sum())

    if fail_count > 0:
        raise SystemExit(f"Validation completed with {fail_count} failure(s).")

    print("\nData quality validation completed successfully.")


if __name__ == "__main__":
    main()