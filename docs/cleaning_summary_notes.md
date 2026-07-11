# Cleaning Summary Notes

## Purpose

This document summarizes the first data cleaning stage for the RetailOps Insight project.

## What Was Cleaned

The raw Online Retail dataset was cleaned and transformed into reporting-ready files.

## Main Cleaning Actions

- Standardized column names to snake_case
- Converted invoice dates into datetime format
- Standardized missing customer IDs as `UNKNOWN`
- Standardized missing product descriptions as `UNKNOWN_DESCRIPTION`
- Identified cancelled invoices using invoice numbers beginning with `C`
- Created transaction status labels:
  - Completed
  - Cancelled/Return
  - Data Issue
- Created reporting fields:
  - line_revenue
  - completed_sales_amount
  - cancelled_amount
  - invoice_year
  - invoice_month
  - invoice_day
  - invoice_hour
  - invoice_year_month
- Created row-level data quality flags
- Created a product master table
- Created a customer master table
- Created a data quality issue log
- Created a cleaning summary report

## Why This Matters

This cleaning process prepares the dataset for:

- SQL analysis
- KPI reporting
- dashboard development
- data quality review
- application support-style issue investigation

## Key Principle

The raw dataset was not overwritten. Cleaned outputs were saved separately in `data/cleaned/`.

