from pathlib import Path
import sqlite3

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATABASE_PATH = PROJECT_ROOT / "data" / "database" / "retailops.db"
SQL_OUTPUT_DIR = PROJECT_ROOT / "reports" / "sql_outputs"


SQL_OUTPUT_TABLES = {
    "executive_kpi_summary.csv": "executive_kpi_summary",
    "data_quality_kpi_summary.csv": "data_quality_kpi_summary",
    "customer_id_coverage.csv": "customer_id_coverage",
    "duplicate_row_summary.csv": "duplicate_row_summary",
    "transaction_status_summary.csv": "transaction_status_summary",
    "unit_price_issue_summary.csv": "unit_price_issue_summary",
}


def check_database_exists() -> None:
    """
    Confirm the SQLite database exists before loading helper tables.
    """
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}. "
            "Run python src/load_to_sqlite.py first."
        )


def load_sql_output_tables(connection: sqlite3.Connection) -> None:
    """
    Load selected SQL output CSV files into SQLite helper tables.
    """
    for file_name, table_name in SQL_OUTPUT_TABLES.items():
        csv_path = SQL_OUTPUT_DIR / file_name

        if not csv_path.exists():
            raise FileNotFoundError(f"Missing SQL output file: {csv_path}")

        df = pd.read_csv(csv_path)

        df.to_sql(
            table_name,
            connection,
            if_exists="replace",
            index=False,
        )

        print(f"Loaded {table_name}: {len(df):,} rows")


def main() -> None:
    """
    Load SQL output CSVs into SQLite for support investigation queries.
    """
    print("Loading SQL output helper tables into SQLite...")

    check_database_exists()

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        load_sql_output_tables(connection)
    finally:
        connection.close()

    print("SQL output helper tables loaded successfully.")


if __name__ == "__main__":
    main()