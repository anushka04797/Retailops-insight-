-- ============================================================
-- RetailOps Insight
-- SQL Analysis: KPI Reporting Logic
-- Purpose:
-- Define and calculate core business KPIs used for reporting,
-- dashboarding, and business review.
-- ============================================================


-- Query 1: Executive KPI Summary
-- Business question:
-- What are the main business KPIs for the full dataset?
WITH totals AS (
    SELECT
        COUNT(*) AS total_transaction_lines,

        SUM(CASE WHEN transaction_status = 'Completed' THEN 1 ELSE 0 END)
            AS completed_transaction_lines,

        SUM(CASE WHEN transaction_status = 'Cancelled/Return' THEN 1 ELSE 0 END)
            AS cancelled_return_lines,

        SUM(CASE WHEN transaction_status = 'Data Issue' THEN 1 ELSE 0 END)
            AS data_issue_lines,

        COUNT(DISTINCT CASE
            WHEN transaction_status = 'Completed' THEN invoice_no
        END) AS completed_invoice_count,

        ROUND(SUM(completed_sales_amount), 2)
            AS total_completed_sales_amount,

        ROUND(SUM(cancelled_amount), 2)
            AS total_cancelled_amount,

        ROUND(SUM(completed_sales_amount) - SUM(cancelled_amount), 2)
            AS net_sales_after_cancellations,

        COUNT(DISTINCT stock_code) AS unique_product_count,

        COUNT(DISTINCT CASE
            WHEN customer_id != 'UNKNOWN' THEN customer_id
        END) AS known_customer_count,

        COUNT(DISTINCT country) AS country_count,

        SUM(CASE WHEN customer_id = 'UNKNOWN' THEN 1 ELSE 0 END)
            AS missing_customer_id_rows,

        SUM(CASE WHEN is_duplicate_row = 1 THEN 1 ELSE 0 END)
            AS duplicate_rows

    FROM transactions
)

SELECT
    total_transaction_lines,
    completed_transaction_lines,
    cancelled_return_lines,
    data_issue_lines,
    completed_invoice_count,
    total_completed_sales_amount,
    total_cancelled_amount,
    net_sales_after_cancellations,

    ROUND(
        total_completed_sales_amount / completed_invoice_count,
        2
    ) AS average_order_value,

    ROUND(
        total_completed_sales_amount / completed_transaction_lines,
        2
    ) AS average_completed_line_value,

    ROUND(
        total_cancelled_amount /
        NULLIF(total_completed_sales_amount + total_cancelled_amount, 0) * 100,
        2
    ) AS cancellation_amount_rate_percent,

    unique_product_count,
    known_customer_count,
    country_count,

    missing_customer_id_rows,

    ROUND(
        missing_customer_id_rows * 100.0 / total_transaction_lines,
        2
    ) AS missing_customer_id_rate_percent,

    duplicate_rows,

    ROUND(
        duplicate_rows * 100.0 / total_transaction_lines,
        2
    ) AS duplicate_row_rate_percent

FROM totals;


-- Query 2: Monthly KPI Summary
-- Business question:
-- How do sales, cancellations, and order volume change by month?
SELECT
    invoice_year_month,

    COUNT(*) AS total_transaction_lines,

    SUM(CASE WHEN transaction_status = 'Completed' THEN 1 ELSE 0 END)
        AS completed_transaction_lines,

    COUNT(DISTINCT CASE
        WHEN transaction_status = 'Completed' THEN invoice_no
    END) AS completed_invoice_count,

    ROUND(SUM(completed_sales_amount), 2)
        AS completed_sales_amount,

    ROUND(SUM(cancelled_amount), 2)
        AS cancelled_amount,

    ROUND(SUM(completed_sales_amount) - SUM(cancelled_amount), 2)
        AS net_sales_after_cancellations,

    ROUND(
        SUM(completed_sales_amount) /
        NULLIF(
            COUNT(DISTINCT CASE
                WHEN transaction_status = 'Completed' THEN invoice_no
            END),
            0
        ),
        2
    ) AS average_order_value,

    SUM(CASE WHEN transaction_status = 'Data Issue' THEN 1 ELSE 0 END)
        AS data_issue_rows

FROM transactions
GROUP BY invoice_year_month
ORDER BY invoice_year_month;


-- Query 3: Data Quality KPI Summary
-- Business question:
-- What are the main data quality risk indicators?
WITH quality_totals AS (
    SELECT
        COUNT(*) AS total_transaction_lines,

        SUM(CASE WHEN customer_id = 'UNKNOWN' THEN 1 ELSE 0 END)
            AS missing_customer_id_rows,

        SUM(CASE WHEN is_duplicate_row = 1 THEN 1 ELSE 0 END)
            AS duplicate_rows,

        SUM(CASE WHEN is_zero_or_negative_unit_price = 1 THEN 1 ELSE 0 END)
            AS zero_or_negative_unit_price_rows,

        SUM(CASE WHEN is_missing_description = 1 THEN 1 ELSE 0 END)
            AS missing_description_rows,

        SUM(CASE WHEN transaction_status = 'Data Issue' THEN 1 ELSE 0 END)
            AS data_issue_rows

    FROM transactions
),

issue_log_total AS (
    SELECT
        COUNT(*) AS data_quality_issue_records
    FROM data_quality_issues
)

SELECT
    qt.total_transaction_lines,
    qt.missing_customer_id_rows,

    ROUND(
        qt.missing_customer_id_rows * 100.0 / qt.total_transaction_lines,
        2
    ) AS missing_customer_id_rate_percent,

    qt.duplicate_rows,

    ROUND(
        qt.duplicate_rows * 100.0 / qt.total_transaction_lines,
        2
    ) AS duplicate_row_rate_percent,

    qt.zero_or_negative_unit_price_rows,
    qt.missing_description_rows,
    qt.data_issue_rows,
    ilt.data_quality_issue_records

FROM quality_totals qt
CROSS JOIN issue_log_total ilt;