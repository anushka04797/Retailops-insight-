from pathlib import Path
import sqlite3
import pandas as pd


DATABASE_DIR = Path("data/database")
DATABASE_PATH = DATABASE_DIR / "retailops.db"

TRANSACTIONS_FILE = Path("data/cleaned/online_retail_transactions_cleaned.csv")
PRODUCTS_FILE = Path("data/cleaned/products_cleaned.csv")
CUSTOMERS_FILE = Path("data/cleaned/customers_cleaned.csv")
DATA_QUALITY_ISSUES_FILE = Path("reports/data_quality/data_quality_issues.csv")
CLEANING_SUMMARY_FILE = Path("reports/data_quality/cleaning_summary.csv")


def ensure_database_directory() -> None:
    """
    Create the database directory if it does not already exist.
    """
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)


def check_required_files() -> None:
    """
    Confirm all required cleaned files exist before loading data.
    """
    required_files = [
        TRANSACTIONS_FILE,
        PRODUCTS_FILE,
        CUSTOMERS_FILE,
        DATA_QUALITY_ISSUES_FILE,
        CLEANING_SUMMARY_FILE,
    ]

    missing_files = [str(file) for file in required_files if not file.exists()]

    if missing_files:
        missing_list = "\n".join(missing_files)
        raise FileNotFoundError(
            f"The following required files are missing:\n{missing_list}"
        )


def get_connection() -> sqlite3.Connection:
    """
    Create and return a SQLite database connection.
    """
    return sqlite3.connect(DATABASE_PATH)


def load_csv_in_chunks(
    connection: sqlite3.Connection,
    csv_path: Path,
    table_name: str,
    chunksize: int = 50000
) -> int:
    """
    Load a large CSV file into SQLite in chunks.

    This avoids loading the entire
    file into memory at once.
    """
    print(f"\nLoading large file into table: {table_name}")
    print(f"Source file: {csv_path}")

    total_rows = 0
    first_chunk = True

    for chunk in pd.read_csv(csv_path, chunksize=chunksize):
        if_exists_mode = "replace" if first_chunk else "append"

        chunk.to_sql(
            table_name,
            connection,
            if_exists=if_exists_mode,
            index=False
        )

        total_rows += len(chunk)
        first_chunk = False

        print(f"Loaded {total_rows:,} rows into {table_name}...")

    print(f"Finished loading {table_name}: {total_rows:,} rows")

    return total_rows


def load_small_csv(
    connection: sqlite3.Connection,
    csv_path: Path,
    table_name: str
) -> int:
    """
    Load a smaller CSV file into SQLite.
    """
    print(f"\nLoading table: {table_name}")
    print(f"Source file: {csv_path}")

    df = pd.read_csv(csv_path)

    df.to_sql(
        table_name,
        connection,
        if_exists="replace",
        index=False
    )

    print(f"Finished loading {table_name}: {len(df):,} rows")

    return len(df)


def create_indexes(connection: sqlite3.Connection) -> None:
    """
    Create indexes on commonly queried columns.

    Indexes make SQL filtering and joins faster.
    """
    print("\nCreating indexes...")

    index_statements = [
        """
        CREATE INDEX IF NOT EXISTS idx_transactions_invoice_date
        ON transactions(invoice_date);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_transactions_invoice_year_month
        ON transactions(invoice_year_month);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_transactions_stock_code
        ON transactions(stock_code);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_transactions_customer_id
        ON transactions(customer_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_transactions_country
        ON transactions(country);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_transactions_status
        ON transactions(transaction_status);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_products_stock_code
        ON products(stock_code);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_customers_customer_id
        ON customers(customer_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_data_quality_raw_row_id
        ON data_quality_issues(raw_row_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_data_quality_issue_type
        ON data_quality_issues(issue_type);
        """,
    ]

    cursor = connection.cursor()

    for statement in index_statements:
        cursor.execute(statement)

    connection.commit()

    print("Indexes created successfully.")


def verify_loaded_tables(connection: sqlite3.Connection) -> pd.DataFrame:
    """
    Verify that expected tables exist and return their row counts.
    """
    print("\nVerifying loaded tables...")

    expected_tables = [
        "transactions",
        "products",
        "customers",
        "data_quality_issues",
        "cleaning_summary",
    ]

    verification_results = []

    for table in expected_tables:
        query = f"SELECT COUNT(*) AS row_count FROM {table};"
        row_count = pd.read_sql_query(query, connection)["row_count"].iloc[0]

        verification_results.append({
            "table_name": table,
            "row_count": int(row_count),
        })

    result_df = pd.DataFrame(verification_results)

    print("\n=== Table Row Counts ===")
    print(result_df.to_string(index=False))

    return result_df


def save_database_load_summary(summary_df: pd.DataFrame) -> None:
    """
    Save database loading verification results as a CSV report.
    """
    output_path = Path("reports/data_quality/database_load_summary.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    summary_df.to_csv(output_path, index=False)

    print(f"\nSaved database load summary: {output_path}")


def main() -> None:
    """
    Main database loading workflow.
    """
    print("Starting SQLite database load process...")

    ensure_database_directory()
    check_required_files()

    if DATABASE_PATH.exists():
        print(f"\nExisting database found and will be replaced: {DATABASE_PATH}")
        DATABASE_PATH.unlink()

    connection = get_connection()

    try:
        load_csv_in_chunks(
            connection=connection,
            csv_path=TRANSACTIONS_FILE,
            table_name="transactions",
            chunksize=50000
        )

        load_small_csv(
            connection=connection,
            csv_path=PRODUCTS_FILE,
            table_name="products"
        )

        load_small_csv(
            connection=connection,
            csv_path=CUSTOMERS_FILE,
            table_name="customers"
        )

        load_small_csv(
            connection=connection,
            csv_path=DATA_QUALITY_ISSUES_FILE,
            table_name="data_quality_issues"
        )

        load_small_csv(
            connection=connection,
            csv_path=CLEANING_SUMMARY_FILE,
            table_name="cleaning_summary"
        )

        create_indexes(connection)

        summary_df = verify_loaded_tables(connection)
        save_database_load_summary(summary_df)

    finally:
        connection.close()

    print("\nSQLite database load completed successfully.")
    print(f"Database created at: {DATABASE_PATH}")


if __name__ == "__main__":
    main()