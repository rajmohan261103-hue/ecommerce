# Power BI dashboard guide

## Import files

Use **Home → Get data → Text/CSV** and import:

- `outputs/transactions_clean.csv`
- `outputs/customer_rfm.csv`
- `outputs/monthly_revenue.csv`
- `outputs/country_revenue.csv`
- `outputs/top_products.csv`
- `outputs/cohort_retention.csv`

Check data types:
- Dates: Date/Time or Date
- Revenue, unit price, monetary: Decimal Number
- Quantity, frequency, recency_days, cohort_index: Whole Number where appropriate
- Customer and invoice IDs: Text

## Suggested model

For a simple portfolio report, use the generated summary tables as separate visuals and the transaction table for detailed analysis. If building a star schema, create shared Date and Customer dimensions and define one-to-many relationships carefully. Avoid creating ambiguous many-to-many relationships.

## Page 1 — Executive Overview

Cards:
- Total Revenue
- Total Orders
- Total Customers
- Average Order Value

Visuals:
- Line chart: `monthly_revenue[invoice_month]` vs `monthly_revenue[revenue]`
- Bar chart: `country_revenue[country]` vs `country_revenue[revenue]` (Top 10)
- Column chart: orders by month

## Page 2 — Customer Insights

Visuals:
- Donut chart: customer count by `customer_rfm[rfm_segment]`
- Bar chart: customer count by `customer_rfm[customer_status]`
- Scatter chart: `frequency` vs `monetary`, with customer ID in details
- Table: customer ID, recency days, frequency, monetary, status, RFM segment

## Page 3 — Product & Geography

Visuals:
- Bar chart: top products by revenue
- Bar chart: revenue by country
- Table: product description, quantity sold, revenue

## Page 4 — Retention

Use `cohort_retention.csv`:
- Rows: `cohort_month`
- Columns: `cohort_index`
- Values: `retention_rate`
- Apply conditional formatting to create a cohort heatmap.

## Slicers

Useful slicers include invoice month, country, customer status, and RFM segment. Make sure slicers affect only visuals where the underlying tables have valid relationships.

## Design tips

- Use a consistent 2–3 colour palette.
- Put the most important KPIs at the top.
- Use clear titles and currency labels (GBP).
- Add a note: "Inactive = no purchase for more than 90 days relative to the dataset snapshot date."
- Add a source note: "Source: UCI Online Retail II; historical data, 2009–2011."

## Final quality checks

- Confirm total revenue equals the sum of transaction-line revenue.
- Use distinct invoice count for orders, not row count.
- Check that customer counts are distinct.
- Verify cohort month 0 retention is 100%.
- Ensure the dashboard communicates historical scope and the project-defined inactivity rule.
