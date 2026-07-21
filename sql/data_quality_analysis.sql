-- ============================================================
-- RetailOps Insight
-- SQL Analysis: Data Quality and Support Investigation
-- Purpose:
-- Analyze data quality issues that may affect reporting accuracy,
-- dashboard reliability, and operational decision-making.
-- ============================================================


-- Query 1: Data quality issue summary
-- Business question:
-- What are the most common data quality problems in the dataset?
SELECT
    issue_type,
    COUNT(*) AS issue_count
FROM data_quality_issues
GROUP BY issue_type
ORDER BY issue_count DESC;


-- Query 2: Missing customer IDs by country
-- Business question:
-- Which countries have the highest number of missing customer IDs?
SELECT
    country,
    COUNT(*) AS missing_customer_rows
FROM transactions
WHERE customer_id = 'UNKNOWN'
GROUP BY country
ORDER BY missing_customer_rows DESC
LIMIT 10;


-- Query 3: Completed sales with missing customer IDs
-- Business question:
-- How much completed sales revenue is linked to missing customer IDs?
SELECT
    CASE
        WHEN customer_id = 'UNKNOWN' THEN 'Missing Customer ID'
        ELSE 'Known Customer ID'
    END AS customer_id_status,
    COUNT(*) AS transaction_lines,
    ROUND(SUM(completed_sales_amount), 2) AS completed_sales_amount
FROM transactions
WHERE transaction_status = 'Completed'
GROUP BY customer_id_status
ORDER BY completed_sales_amount DESC;


-- Query 4: Duplicate row summary
-- Business question:
-- How many rows appear duplicated, and what is their possible revenue impact?
SELECT
    is_duplicate_row,
    COUNT(*) AS row_count,
    ROUND(SUM(completed_sales_amount), 2) AS completed_sales_amount
FROM transactions
GROUP BY is_duplicate_row
ORDER BY row_count DESC;


-- Query 5: Cancelled/returns by country
-- Business question:
-- Which countries have the highest cancelled/return amount?
SELECT
    country,
    COUNT(*) AS cancelled_return_lines,
    ROUND(SUM(cancelled_amount), 2) AS total_cancelled_amount
FROM transactions
WHERE transaction_status = 'Cancelled/Return'
GROUP BY country
ORDER BY total_cancelled_amount DESC
LIMIT 10;


-- Query 6: Zero or negative unit price issue summary
-- Business question:
-- How many rows have invalid unit price values?
SELECT
    is_zero_or_negative_unit_price,
    COUNT(*) AS row_count,
    ROUND(SUM(line_revenue), 2) AS raw_line_revenue
FROM transactions
GROUP BY is_zero_or_negative_unit_price
ORDER BY row_count DESC;


-- Query 7: Data issue rows by month
-- Business question:
-- Are data issue rows concentrated in specific months?
SELECT
    invoice_year_month,
    COUNT(*) AS data_issue_rows
FROM transactions
WHERE transaction_status = 'Data Issue'
GROUP BY invoice_year_month
ORDER BY data_issue_rows DESC;


-- Query 8: Top invoices with multiple issue records
-- Business question:
-- Which invoices appear most often in the data quality issue log?
SELECT
    invoice_no,
    COUNT(*) AS issue_records
FROM data_quality_issues
GROUP BY invoice_no
ORDER BY issue_records DESC
LIMIT 10;