# E-Commerce Customer Retention & Revenue Analytics

An end-to-end data analytics portfolio project using the **UCI Online Retail II** transaction dataset. The project demonstrates data cleaning, SQL analysis, Python-based customer analytics, and a Power BI reporting workflow.

> **Important:** This is a historical dataset (December 2009–December 2011), not live business data. The project uses a transparent **90-day inactivity proxy** to flag customers as "At Risk" or "Inactive"; it does not claim to observe a company's official churn labels.

## Business problem

An online retailer wants to understand customer purchasing patterns, revenue performance, repeat purchasing, and customer inactivity. The analysis is designed to help answer:

1. How are revenue and order volumes changing over time?
2. Which countries and products contribute the most revenue?
3. How concentrated is revenue among customers?
4. Which customers are high-value, loyal, at risk, or inactive?
5. How does customer retention change by first-purchase cohort?
6. What actions could improve repeat purchasing?

## Dataset

- **Source:** [UCI Machine Learning Repository – Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii)
- **Creator:** Daqing Chen
- **Coverage:** 1 December 2009 to 9 December 2011
- **Records:** 1,067,371 transaction lines
- **Fields:** `Invoice`, `StockCode`, `Description`, `Quantity`, `InvoiceDate`, `Price`, `Customer ID`, `Country`
- **License:** CC BY 4.0. Credit the original source when sharing derived work.

Download `online_retail_II.xlsx` from the UCI page and place it in `data/`. The workbook is intentionally not included in this Git repository because it is large and belongs to the original dataset publisher.

Expected local path:

```text
data/online_retail_II.xlsx
```

See [`data/README.md`](data/README.md) for details.

## Repository structure

```text
ecommerce-customer-retention-analytics/
├── data/
│   └── README.md
├── docs/
│   └── powerbi_dashboard_guide.md
├── outputs/
│   └── .gitkeep
├── powerbi/
│   └── measures.dax
├── sql/
│   └── analysis.sql
├── src/
│   └── analyze.py
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup

Python 3.10+ is recommended.

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/ecommerce-customer-retention-analytics.git
cd ecommerce-customer-retention-analytics
```

### 2. Create and activate a virtual environment (optional but recommended)

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Download the dataset

Download the Excel workbook from the UCI link above and save it as:

```text
data/online_retail_II.xlsx
```

### 5. Run the analysis

From the project root:

```bash
python src/analyze.py
```

The script reads all sheets in the workbook, combines them, cleans the transaction lines, and writes analysis-ready CSV files into `outputs/`.

## Data preparation decisions

The script:

- Standardizes the source column names.
- Parses invoice dates and numeric fields.
- Removes rows without a customer ID, invoice number, or usable product code.
- Excludes cancellation invoices (invoice numbers beginning with `C`) and non-positive quantity/price rows from the positive-sales analysis.
- Removes exact duplicate rows.
- Calculates `Revenue = Quantity × UnitPrice`.
- Keeps the original currency context: **British pounds (£)**.

Returns and cancellations are excluded from the positive-sales KPIs in this starter project. A production analysis should separately quantify refunds and returns rather than treating them as ordinary sales.

## Customer inactivity definition

The analysis uses the day after the latest valid transaction date as the snapshot date. A customer is flagged as:

- **Active:** last purchase was within 30 days of the snapshot.
- **At Risk:** last purchase was 31–90 days before the snapshot.
- **Inactive (90+ days):** last purchase was more than 90 days before the snapshot.

These are analytical thresholds chosen for this project, not labels supplied by UCI or the retailer. Change the thresholds only if you explain and justify the business rule.

## Generated outputs

| File | Description |
|---|---|
| `transactions_clean.csv` | Clean transaction-level data |
| `customer_rfm.csv` | Customer-level Recency, Frequency, Monetary value and segment |
| `monthly_revenue.csv` | Monthly revenue and invoice counts |
| `country_revenue.csv` | Revenue by country |
| `top_products.csv` | Top products by revenue |
| `cohort_retention.csv` | Monthly customer cohort retention table |

## SQL analysis

The SQL file [`sql/analysis.sql`](sql/analysis.sql) contains SQLite-compatible table creation and example business queries. To use it:

1. Run the Python script to create `outputs/transactions_clean.csv`.
2. Import that CSV into a SQLite database table named `transactions`.
3. Run the SQL queries in `sql/analysis.sql`.

The script exports dates as ISO-like text values so they can be parsed by SQLite date functions.

## Power BI dashboard

Follow [`docs/powerbi_dashboard_guide.md`](docs/powerbi_dashboard_guide.md) to import the generated CSVs, create relationships/measures, and build the report.

Suggested report pages:

1. **Executive Overview:** revenue, orders, customers, average order value, monthly trend.
2. **Customer Insights:** RFM segments, inactive customers, customer value distribution.
3. **Product & Geography:** top products and country revenue.
4. **Retention:** cohort retention matrix.

Add screenshots of your completed dashboard to a `screenshots/` folder before publishing your final GitHub version.

## Key business recommendations to investigate

Do not copy recommendations without validating them against your results. Examples of questions to investigate:

- Could a targeted win-back campaign help customers inactive for more than 90 days?
- Are a small number of customers contributing a large share of revenue?
- Which high-revenue products could be featured in repeat-purchase campaigns?
- Do some acquisition cohorts show stronger repeat purchasing than others?

## Limitations

- Historical transactions only; findings should not be presented as current market behaviour.
- No supplied churn outcome or customer demographics are available.
- The 90-day inactivity label is a project-defined proxy, not verified churn.
- Revenue is calculated from quantity multiplied by unit price and is expressed in GBP.
- The dataset is transaction-line level; invoice counts must use distinct invoice numbers.

## Dataset citation

Chen, D. (2012). *Online Retail II* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5CG6D

Dataset page: https://archive.ics.uci.edu/dataset/502/online+retail+ii

## Author

**Your Name**  
Aspiring Data Analyst | SQL | Python | Excel | Power BI

Replace this section with your LinkedIn and GitHub profile links. Only publish results you have personally run, checked, and can explain in an interview.
