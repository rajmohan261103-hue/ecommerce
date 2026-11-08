-- E-Commerce Customer Retention & Revenue Analytics
-- SQL dialect: SQLite
-- Import outputs/transactions_clean.csv into a table named transactions first.

-- 1. Suggested table schema
CREATE TABLE IF NOT EXISTS transactions (
    invoice TEXT,
    stock_code TEXT,
    description TEXT,
    quantity REAL,
    invoice_date TEXT,
    invoice_month TEXT,
    unit_price REAL,
    customer_id TEXT,
    country TEXT,
    revenue REAL
);

-- 2. Overall business KPIs
SELECT
    ROUND(SUM(revenue), 2) AS total_revenue_gbp,
    COUNT(DISTINCT invoice) AS total_orders,
    COUNT(DISTINCT customer_id) AS unique_customers,
    ROUND(SUM(revenue) / COUNT(DISTINCT invoice), 2) AS average_order_value_gbp
FROM transactions;

-- 3. Monthly revenue trend
SELECT
    invoice_month,
    ROUND(SUM(revenue), 2) AS monthly_revenue_gbp,
    COUNT(DISTINCT invoice) AS orders,
    COUNT(DISTINCT customer_id) AS customers
FROM transactions
GROUP BY invoice_month
ORDER BY invoice_month;

-- 4. Top 10 countries by revenue
SELECT
    country,
    ROUND(SUM(revenue), 2) AS revenue_gbp,
    COUNT(DISTINCT invoice) AS orders,
    COUNT(DISTINCT customer_id) AS customers
FROM transactions
GROUP BY country
ORDER BY revenue_gbp DESC
LIMIT 10;

-- 5. Top 10 products by revenue
SELECT
    stock_code,
    description,
    ROUND(SUM(revenue), 2) AS revenue_gbp,
    SUM(quantity) AS units_sold
FROM transactions
GROUP BY stock_code, description
ORDER BY revenue_gbp DESC
LIMIT 10;

-- 6. Customer-level RFM metrics
WITH customer_metrics AS (
    SELECT
        customer_id,
        MAX(date(invoice_date)) AS last_purchase_date,
        COUNT(DISTINCT invoice) AS frequency,
        ROUND(SUM(revenue), 2) AS monetary
    FROM transactions
    GROUP BY customer_id
),
snapshot AS (
    SELECT date(MAX(invoice_date), '+1 day') AS snapshot_date
    FROM transactions
)
SELECT
    c.customer_id,
    CAST(julianday(s.snapshot_date) - julianday(c.last_purchase_date) AS INTEGER) AS recency_days,
    c.frequency,
    c.monetary
FROM customer_metrics c
CROSS JOIN snapshot s
ORDER BY c.monetary DESC;

-- 7. Customer inactivity proxy (90+ days since last purchase)
-- This is a project-defined proxy, not an official churn label.
WITH customer_last_purchase AS (
    SELECT customer_id, MAX(date(invoice_date)) AS last_purchase_date
    FROM transactions
    GROUP BY customer_id
),
snapshot AS (
    SELECT date(MAX(invoice_date), '+1 day') AS snapshot_date
    FROM transactions
)
SELECT
    CASE
        WHEN julianday(s.snapshot_date) - julianday(c.last_purchase_date) <= 30 THEN 'Active'
        WHEN julianday(s.snapshot_date) - julianday(c.last_purchase_date) <= 90 THEN 'At Risk'
        ELSE 'Inactive (90+ days)'
    END AS customer_status,
    COUNT(*) AS customer_count
FROM customer_last_purchase c
CROSS JOIN snapshot s
GROUP BY customer_status
ORDER BY customer_count DESC;

-- 8. Repeat-purchase customers
SELECT
    COUNT(*) AS repeat_customers
FROM (
    SELECT customer_id
    FROM transactions
    GROUP BY customer_id
    HAVING COUNT(DISTINCT invoice) > 1
);

-- 9. Revenue concentration by customer
WITH customer_revenue AS (
    SELECT customer_id, SUM(revenue) AS customer_revenue
    FROM transactions
    GROUP BY customer_id
)
SELECT
    customer_id,
    ROUND(customer_revenue, 2) AS customer_revenue_gbp,
    ROUND(
        100.0 * customer_revenue / (SELECT SUM(customer_revenue) FROM customer_revenue),
        2
    ) AS revenue_share_pct
FROM customer_revenue
ORDER BY customer_revenue DESC
LIMIT 20;

-- 10. Cohort retention (monthly first purchase vs active purchase month)
WITH customer_months AS (
    SELECT DISTINCT
        customer_id,
        date(invoice_date, 'start of month') AS order_month
    FROM transactions
),
cohorts AS (
    SELECT customer_id, MIN(order_month) AS cohort_month
    FROM customer_months
    GROUP BY customer_id
),
activity AS (
    SELECT
        cm.customer_id,
        c.cohort_month,
        cm.order_month,
        (
            (CAST(strftime('%Y', cm.order_month) AS INTEGER) -
             CAST(strftime('%Y', c.cohort_month) AS INTEGER)) * 12
            +
            (CAST(strftime('%m', cm.order_month) AS INTEGER) -
             CAST(strftime('%m', c.cohort_month) AS INTEGER))
        ) AS cohort_index
    FROM customer_months cm
    JOIN cohorts c ON cm.customer_id = c.customer_id
),
cohort_counts AS (
    SELECT cohort_month, cohort_index, COUNT(DISTINCT customer_id) AS customers
    FROM activity
    GROUP BY cohort_month, cohort_index
),
cohort_sizes AS (
    SELECT cohort_month, customers AS cohort_size
    FROM cohort_counts
    WHERE cohort_index = 0
)
SELECT
    cc.cohort_month,
    cc.cohort_index,
    cc.customers,
    cs.cohort_size,
    ROUND(1.0 * cc.customers / cs.cohort_size, 4) AS retention_rate
FROM cohort_counts cc
JOIN cohort_sizes cs USING (cohort_month)
ORDER BY cc.cohort_month, cc.cohort_index;
