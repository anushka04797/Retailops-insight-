-- ============================================================
-- RetailOps Insight
-- SQL Analysis: Support Ticket Investigation
-- Purpose:
-- Investigate reporting support tickets using KPI, transaction,
-- and data quality tables.
-- ============================================================


-- Query 1: Support ticket summary by category and priority
-- Business question:
-- What types of reporting/support issues were logged?
SELECT
    category,
    priority,
    COUNT(*) AS ticket_count
FROM support_tickets
GROUP BY
    category,
    priority
ORDER BY
    ticket_count DESC,
    priority;


-- Query 2: High-priority support tickets
-- Business question:
-- Which issues should be reviewed first?
SELECT
    ticket_id,
    category,
    priority,
    affected_report,
    issue_summary,
    linked_metric,
    current_status
FROM support_tickets
WHERE priority = 'High'
ORDER BY ticket_id;


-- Query 3: RPT-001 revenue reconciliation
-- Business question:
-- Why does net sales not match completed sales?
SELECT
    st.ticket_id,
    st.category,
    st.affected_report,
    st.issue_summary,
    ek.total_completed_sales_amount,
    ek.total_cancelled_amount,
    ek.net_sales_after_cancellations,
    ROUND(
        ek.total_completed_sales_amount - ek.total_cancelled_amount,
        2
    ) AS recalculated_net_sales,
    CASE
        WHEN ROUND(
            ek.total_completed_sales_amount - ek.total_cancelled_amount,
            2
        ) = ek.net_sales_after_cancellations
        THEN 'Net sales matches completed sales minus cancelled amount'
        ELSE 'Net sales mismatch requires investigation'
    END AS investigation_result
FROM support_tickets st
CROSS JOIN executive_kpi_summary ek
WHERE st.ticket_id = 'RPT-001';


-- Query 4: RPT-002 missing customer ID impact
-- Business question:
-- How much reporting risk exists because customer IDs are missing?
SELECT
    st.ticket_id,
    st.category,
    st.affected_report,
    st.issue_summary,
    dq.missing_customer_id_rows,
    dq.missing_customer_id_rate_percent,
    cc.customer_id_status,
    cc.transaction_lines,
    cc.completed_sales_amount
FROM support_tickets st
CROSS JOIN data_quality_kpi_summary dq
LEFT JOIN customer_id_coverage cc
    ON cc.customer_id_status = 'Missing Customer ID'
WHERE st.ticket_id = 'RPT-002';


-- Query 5: RPT-003 duplicate row impact
-- Business question:
-- What is the possible reporting impact of duplicate-flagged rows?
SELECT
    st.ticket_id,
    st.category,
    st.affected_report,
    st.issue_summary,
    drs.is_duplicate_row,
    drs.row_count,
    drs.completed_sales_amount
FROM support_tickets st
CROSS JOIN duplicate_row_summary drs
WHERE st.ticket_id = 'RPT-003'
  AND drs.is_duplicate_row = 1;


-- Query 6: RPT-004 cancellation amount explanation
-- Business question:
-- What is the cancellation/return amount being separated from completed sales?
SELECT
    st.ticket_id,
    st.category,
    st.affected_report,
    st.issue_summary,
    tss.transaction_status,
    tss.row_count,
    tss.completed_sales_amount,
    tss.cancelled_amount
FROM support_tickets st
CROSS JOIN transaction_status_summary tss
WHERE st.ticket_id = 'RPT-004'
  AND tss.transaction_status = 'Cancelled/Return';


-- Query 7: RPT-005 invalid pricing issue review
-- Business question:
-- How many rows have zero or negative unit price values?
SELECT
    st.ticket_id,
    st.category,
    st.affected_report,
    st.issue_summary,
    upis.is_zero_or_negative_unit_price,
    upis.row_count,
    upis.raw_line_revenue
FROM support_tickets st
CROSS JOIN unit_price_issue_summary upis
WHERE st.ticket_id = 'RPT-005'
  AND upis.is_zero_or_negative_unit_price = 1;


-- Query 8: Support ticket investigation recommendation
-- Business question:
-- What recommended action should be taken for each support ticket?
SELECT
    ticket_id,
    category,
    priority,
    affected_report,
    linked_metric,
    CASE
        WHEN ticket_id = 'RPT-001'
            THEN 'Clarify KPI definitions: completed sales and net sales are different metrics.'
        WHEN ticket_id = 'RPT-002'
            THEN 'Add customer ID coverage note to customer-level reports.'
        WHEN ticket_id = 'RPT-003'
            THEN 'Keep duplicate row monitor visible in data quality dashboard.'
        WHEN ticket_id = 'RPT-004'
            THEN 'Document cancellation/return logic beside revenue KPIs.'
        WHEN ticket_id = 'RPT-005'
            THEN 'Exclude invalid pricing rows from completed sales and monitor count.'
        WHEN ticket_id = 'RPT-006'
            THEN 'Provide summarized issue counts in addition to row-level issue logs.'
        ELSE 'Review ticket manually.'
    END AS recommended_action
FROM support_tickets
ORDER BY ticket_id;