"""Prepare UCI Online Retail II data and generate customer analytics outputs."""

from pathlib import Path
import argparse
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "online_retail_II.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

COLUMN_MAP = {
    "Invoice": "invoice",
    "InvoiceNo": "invoice",
    "StockCode": "stock_code",
    "Description": "description",
    "Quantity": "quantity",
    "InvoiceDate": "invoice_date",
    "Price": "unit_price",
    "UnitPrice": "unit_price",
    "Customer ID": "customer_id",
    "CustomerID": "customer_id",
    "Country": "country",
}


def load_workbook(path: Path) -> pd.DataFrame:
    """Read and combine all workbook sheets."""
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}\n"
            "Download online_retail_II.xlsx from the UCI dataset page "
            "and place it in the data/ folder."
        )

    sheets = pd.read_excel(path, sheet_name=None, engine="openpyxl")
    frames = []
    for sheet_name, frame in sheets.items():
        if frame is not None and not frame.empty:
            frame["source_sheet"] = sheet_name
            frames.append(frame)

    if not frames:
        raise ValueError("No non-empty worksheets were found in the Excel file.")

    data = pd.concat(frames, ignore_index=True)
    data.columns = [str(c).strip() for c in data.columns]
    return data


def clean_transactions(raw: pd.DataFrame) -> pd.DataFrame:
    """Standardize fields and retain valid positive sales lines."""
    rename = {col: COLUMN_MAP[col] for col in raw.columns if col in COLUMN_MAP}
    df = raw.rename(columns=rename).copy()

    required = [
        "invoice", "stock_code", "description", "quantity",
        "invoice_date", "unit_price", "customer_id", "country"
    ]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(
            f"Expected columns not found: {missing}. "
            f"Columns present: {list(df.columns)}"
        )

    df = df[required].copy()
    df["invoice"] = df["invoice"].astype("string").str.strip()
    df["stock_code"] = df["stock_code"].astype("string").str.strip()
    df["description"] = df["description"].astype("string").str.strip()
    df["country"] = df["country"].astype("string").str.strip()

    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["customer_id"] = pd.to_numeric(df["customer_id"], errors="coerce")
    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")

    df = df.dropna(subset=[
        "invoice", "stock_code", "invoice_date", "quantity",
        "unit_price", "customer_id", "country"
    ])

    # Customer IDs are identifiers, not quantities.
    df["customer_id"] = df["customer_id"].astype("int64").astype(str)
    df["is_cancellation"] = df["invoice"].str.upper().str.startswith("C", na=False)

    # This starter analysis focuses on positive sales. Cancellations/returns
    # should be analyzed separately in a dedicated returns analysis.
    df = df.loc[~df["is_cancellation"]].copy()
    df = df.loc[(df["quantity"] > 0) & (df["unit_price"] > 0)].copy()
    df = df.drop_duplicates()
    df["revenue"] = df["quantity"] * df["unit_price"]
    df["invoice_date"] = df["invoice_date"].dt.strftime("%Y-%m-%d %H:%M:%S")
    df["invoice_month"] = pd.to_datetime(df["invoice_date"]).dt.to_period("M").astype(str)

    return df[[
        "invoice", "stock_code", "description", "quantity", "invoice_date",
        "invoice_month", "unit_price", "customer_id", "country", "revenue"
    ]]


def build_rfm(transactions: pd.DataFrame) -> pd.DataFrame:
    """Calculate RFM and transparent inactivity segments."""
    df = transactions.copy()
    df["invoice_date"] = pd.to_datetime(df["invoice_date"])
    snapshot_date = df["invoice_date"].max().normalize() + pd.Timedelta(days=1)

    rfm = df.groupby("customer_id").agg(
        last_purchase=("invoice_date", "max"),
        frequency=("invoice", "nunique"),
        monetary=("revenue", "sum"),
        total_items=("quantity", "sum"),
    ).reset_index()

    rfm["recency_days"] = (snapshot_date - rfm["last_purchase"].dt.normalize()).dt.days
    rfm["customer_status"] = np.select(
        [
            rfm["recency_days"] <= 30,
            rfm["recency_days"] <= 90,
        ],
        ["Active", "At Risk"],
        default="Inactive (90+ days)",
    )

    # Rank-based scores avoid assuming equal-sized business intervals.
    rfm["r_score"] = pd.qcut(
        rfm["recency_days"].rank(method="first", ascending=False),
        5, labels=[1, 2, 3, 4, 5]
    ).astype(int)
    rfm["f_score"] = pd.qcut(
        rfm["frequency"].rank(method="first"),
        5, labels=[1, 2, 3, 4, 5]
    ).astype(int)
    rfm["m_score"] = pd.qcut(
        rfm["monetary"].rank(method="first"),
        5, labels=[1, 2, 3, 4, 5]
    ).astype(int)

    def segment(row):
        if row["r_score"] >= 4 and row["f_score"] >= 4 and row["m_score"] >= 4:
            return "Champions"
        if row["f_score"] >= 4 and row["r_score"] >= 3:
            return "Loyal Customers"
        if row["r_score"] <= 2 and row["f_score"] >= 3:
            return "At Risk - Previously Valuable"
        if row["r_score"] <= 2:
            return "Needs Attention"
        return "Potential Loyalists"

    rfm["rfm_segment"] = rfm.apply(segment, axis=1)
    rfm["snapshot_date"] = snapshot_date.strftime("%Y-%m-%d")
    rfm["last_purchase"] = rfm["last_purchase"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return rfm


def build_monthly_revenue(transactions: pd.DataFrame) -> pd.DataFrame:
    df = transactions.copy()
    return df.groupby("invoice_month").agg(
        revenue=("revenue", "sum"),
        orders=("invoice", "nunique"),
        customers=("customer_id", "nunique"),
        items_sold=("quantity", "sum"),
    ).reset_index().sort_values("invoice_month")


def build_country_revenue(transactions: pd.DataFrame) -> pd.DataFrame:
    return transactions.groupby("country").agg(
        revenue=("revenue", "sum"),
        orders=("invoice", "nunique"),
        customers=("customer_id", "nunique"),
    ).reset_index().sort_values("revenue", ascending=False)


def build_top_products(transactions: pd.DataFrame, limit: int = 20) -> pd.DataFrame:
    return transactions.groupby(["stock_code", "description"]).agg(
        revenue=("revenue", "sum"),
        quantity_sold=("quantity", "sum"),
        orders=("invoice", "nunique"),
    ).reset_index().sort_values("revenue", ascending=False).head(limit)


def build_cohort_retention(transactions: pd.DataFrame) -> pd.DataFrame:
    """Create a monthly cohort retention table (period 0 is 100%)."""
    df = transactions.copy()
    df["invoice_date"] = pd.to_datetime(df["invoice_date"])
    df["order_month"] = df["invoice_date"].dt.to_period("M")
    first_purchase = df.groupby("customer_id")["order_month"].min().rename("cohort_month")
    df = df.join(first_purchase, on="customer_id")
    df["cohort_index"] = (
        (df["order_month"].dt.year - df["cohort_month"].dt.year) * 12
        + (df["order_month"].dt.month - df["cohort_month"].dt.month)
    )
    counts = df.groupby(["cohort_month", "cohort_index"])["customer_id"].nunique()
    cohort_sizes = counts.groupby(level=0).first()
    retention = (counts / cohort_sizes).rename("retention_rate").reset_index()
    retention["cohort_month"] = retention["cohort_month"].astype(str)
    return retention.sort_values(["cohort_month", "cohort_index"])


def main():
    parser = argparse.ArgumentParser(description="Run e-commerce customer analytics.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT,
                        help="Path to the UCI Excel workbook.")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    raw = load_workbook(args.input)
    clean = clean_transactions(raw)

    if clean.empty:
        raise ValueError("No valid positive-sales transactions remain after cleaning.")

    rfm = build_rfm(clean)
    monthly = build_monthly_revenue(clean)
    countries = build_country_revenue(clean)
    products = build_top_products(clean)
    cohorts = build_cohort_retention(clean)

    outputs = {
        "transactions_clean.csv": clean,
        "customer_rfm.csv": rfm,
        "monthly_revenue.csv": monthly,
        "country_revenue.csv": countries,
        "top_products.csv": products,
        "cohort_retention.csv": cohorts,
    }

    for filename, frame in outputs.items():
        frame.to_csv(OUTPUT_DIR / filename, index=False)

    print("\nAnalysis completed successfully.")
    print(f"Clean transaction lines: {len(clean):,}")
    print(f"Unique customers: {clean['customer_id'].nunique():,}")
    print(f"Unique invoices: {clean['invoice'].nunique():,}")
    print(f"Total revenue (GBP): £{clean['revenue'].sum():,.2f}")
    print(f"Output folder: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
