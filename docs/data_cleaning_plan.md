# Data Cleaning Plan

## Project

RetailOps Insight — Retail Operations Analytics, Data Quality, and Support Dashboard

## Raw Dataset

Main dataset: Online Retail transactional sales data.

## Cleaning Objective

The goal is to prepare the raw retail transaction data for SQL analysis, KPI reporting, dashboarding, and support-style issue investigation.

The cleaning process should preserve the original raw file while creating cleaned, analysis-ready outputs.

## Key Raw Columns

| Raw Column | Meaning |
|---|---|
| InvoiceNo | Invoice or cancellation identifier |
| StockCode | Product/item code |
| Description | Product description |
| Quantity | Number of units purchased or returned |
| InvoiceDate | Date and time of invoice |
| UnitPrice | Unit price of item |
| CustomerID | Customer identifier |
| Country | Customer country |

## Cleaning Rules

### 1. Preserve raw data

The original Excel file must remain unchanged in `data/raw/`.

### 2. Standardize column names

Convert column names to snake_case:

- InvoiceNo → invoice_no
- StockCode → stock_code
- Description → description
- Quantity → quantity
- InvoiceDate → invoice_date
- UnitPrice → unit_price
- CustomerID → customer_id
- Country → country

### 3. Clean text fields

- Trim leading/trailing spaces
- Standardize missing descriptions as `UNKNOWN_DESCRIPTION`
- Standardize missing customer IDs as `UNKNOWN`

### 4. Handle invoice and transaction status

Invoices beginning with `C` usually represent cancellations.

Transaction status logic:

| Condition | Status |
|---|---|
| Invoice starts with C or quantity is negative | Cancelled/Return |
| Quantity is zero or unit price is zero/negative | Data Issue |
| Otherwise | Completed |

### 5. Create calculated fields

- line_revenue = quantity × unit_price
- completed_sales_amount = line_revenue only for completed transactions
- cancelled_amount = absolute value of line_revenue for cancelled/return transactions

### 6. Add date fields

Create:

- invoice_year
- invoice_month
- invoice_day
- invoice_hour
- invoice_year_month

### 7. Create data quality flags

Flag rows with:

- missing customer ID
- missing description
- duplicate rows
- negative quantity
- zero or negative unit price
- cancelled invoice
- invalid invoice date

### 8. Create cleaned outputs

The script should produce:

| Output File | Purpose |
|---|---|
| data/cleaned/online_retail_transactions_cleaned.csv | Main cleaned transaction table |
| data/cleaned/products_cleaned.csv | Product master-style table |
| data/cleaned/customers_cleaned.csv | Customer master-style table |
| reports/data_quality/data_quality_issues.csv | Row-level data quality issue log |
| reports/data_quality/cleaning_summary.csv | Summary of cleaning results |

## Reporting Use

For revenue and sales KPIs, use `completed_sales_amount`, not raw `line_revenue`.

For support/data-quality investigation, use the data quality issue log and transaction status fields.

## Notes

This project intentionally keeps cancellations, missing customer rows, and data quality issues visible instead of silently deleting them. This reflects real workplace reporting and application support practice.