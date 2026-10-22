"""
Clean the raw source extracts and build the star schema used by Power BI.

Input : data/raw/      (see generate_sales_data.py)
Output: data/processed/ FactSales.csv, FactSalesTarget.csv, DimDate.csv, DimProduct.csv,
        DimCustomer.csv, DimGeography.csv, DimSalesChannel.csv, cleaning_log.json

Every cleaning rule is logged with the number of rows affected, so the cleaning
workflow is auditable (see docs/data_cleaning.md).

Usage:
    python scripts/prepare_data.py [--raw-dir data/raw] [--out-dir data/processed]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schema import columns  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EXTRACT_DATE = pd.Timestamp("2025-12-31")
CALENDAR_START, CALENDAR_END = pd.Timestamp("2023-01-01"), pd.Timestamp("2025-12-31")

CHANNEL_MAP = {  # every spelling seen in source systems -> conformed channel name
    "online store": "Online Store", "online": "Online Store", "web store": "Online Store",
    "retail stores": "Retail Stores", "retail": "Retail Stores", "store": "Retail Stores",
    "marketplace": "Marketplace", "market place": "Marketplace", "3p marketplace": "Marketplace",
    "b2b wholesale": "B2B Wholesale", "wholesale": "B2B Wholesale", "b2b": "B2B Wholesale",
}
CHANNEL_DIM = [  # key, code, name, type
    (1, "ONL", "Online Store", "Direct - Digital"),
    (2, "RTL", "Retail Stores", "Direct - Physical"),
    (3, "MKT", "Marketplace", "Third-Party"),
    (4, "B2B", "B2B Wholesale", "Wholesale"),
]
REGION_MAP = {"northeast": "Northeast", "midwest": "Midwest", "mid-west": "Midwest",
              "south": "South", "west": "West"}


class CleaningLog:
    def __init__(self) -> None:
        self.steps: list[dict] = []

    def add(self, step: str, rows: int, detail: str) -> None:
        self.steps.append({"step": step, "rows_affected": int(rows), "detail": detail})
        print(f"  [{rows:>6,}] {step}: {detail}")


def parse_money(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.str.replace(r"[$,]", "", regex=True), errors="raise")


def canon_text(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.replace(r"\s+", " ", regex=True)


def clean_orders(raw_dir: Path, log: CleaningLog, products: pd.DataFrame) -> pd.DataFrame:
    df = pd.read_csv(raw_dir / "orders_export_2023_2025.csv", dtype=str, keep_default_na=False)
    log.add("load", len(df), "Raw order-line export rows loaded as text")

    # 1. exact duplicates
    before = len(df)
    df = df.drop_duplicates()
    log.add("remove_exact_duplicates", before - len(df), "Identical rows re-sent by the export were removed")

    # 2. test accounts
    test = df["Customer ID"].str.startswith("C-TEST")
    log.add("remove_test_accounts", test.sum(), "Internal test-account lines (C-TEST-*) removed")
    df = df[~test].copy()

    # 3. trim / standardise text
    for col in ["Customer Name", "Customer Segment", "City", "State", "Region", "Sales Channel",
                "Product Name", "Category", "Sub-Category", "Order Status"]:
        df[col] = canon_text(df[col])
    canon_cats = set(products["Category"])
    cat_lookup = {c.lower(): c for c in canon_cats}
    bad_cat = ~df["Category"].isin(canon_cats)
    df["Category"] = df["Category"].str.lower().map(cat_lookup)
    log.add("standardise_category_text", bad_cat.sum(), "Category casing variants (e.g. 'FURNITURE', 'electronics') mapped to conformed names after trimming")
    if df["Category"].isna().any():
        raise ValueError("Unmapped category values remain")

    bad_reg = ~df["Region"].isin(set(REGION_MAP.values()))
    df["Region"] = df["Region"].str.lower().map(REGION_MAP)
    log.add("standardise_region_text", bad_reg.sum(), "Region casing variants mapped to conformed names after trimming")

    conformed_channels = {c[2] for c in CHANNEL_DIM}
    bad_ch = ~df["Sales Channel"].isin(conformed_channels)
    df["Sales Channel"] = df["Sales Channel"].str.lower().map(CHANNEL_MAP)
    log.add("standardise_channel_names", bad_ch.sum(), "Legacy channel names (e.g. 'Web Store', 'Wholesale') mapped to 4 conformed channels")
    if df["Sales Channel"].isna().any() or df["Region"].isna().any():
        raise ValueError("Unmapped channel or region values remain")

    # 4. product attributes must agree with the product master (master wins)
    m = df.merge(products[["ProductID", "ProductName", "Category", "Subcategory"]],
                 left_on="Product ID", right_on="ProductID", how="left", validate="many_to_one")
    if m["ProductID"].isna().any():
        raise ValueError("Order lines reference unknown products")
    mismatch = (m["Product Name"] != m["ProductName"]) | (m["Category_x"] != m["Category_y"]) | \
               (m["Sub-Category"] != m["Subcategory"])
    log.add("conform_product_attributes", mismatch.sum(), "Lines whose product name/category disagreed with the product master")

    # 5. types
    df["OrderDate"] = pd.to_datetime(df["Order Date"], format="%m/%d/%Y")
    df["ShipDate"] = pd.to_datetime(df["Ship Date"].replace("", np.nan), format="%m/%d/%Y")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="raise").astype(int)
    df["UnitPrice"] = parse_money(df["Unit Price"])
    df["UnitCost"] = parse_money(df["Unit Cost"])
    df["DiscountPct"] = pd.to_numeric(df["Discount"].str.rstrip("%"), errors="raise") / 100
    df["ReportedLineTotal"] = parse_money(df["Line Total"])
    df["OrderLineNumber"] = pd.to_numeric(df["Order Line"]).astype(int)
    log.add("convert_types", len(df), "Parsed US dates (MM/DD/YYYY), currency text ($1,234.56) and percent text (15%)")

    # 6. date rules
    blank_ship = df["ShipDate"].isna()
    if not (df.loc[blank_ship, "Order Status"] == "Open").all():
        raise ValueError("Blank ship date on a non-open order")
    log.add("open_orders_blank_ship_date", blank_ship.sum(), "Blank ship dates kept as blank: orders still open at the 2025-12-31 extract (not imputed)")
    if (df["ShipDate"] < df["OrderDate"]).any() or (df["OrderDate"] > EXTRACT_DATE).any():
        raise ValueError("Impossible dates found")

    # 7. business-key uniqueness after de-duplication
    dup_key = df.duplicated(["Order ID", "OrderLineNumber"], keep=False)
    if dup_key.any():
        raise ValueError(f"{dup_key.sum()} rows share an OrderID+Line with different content")

    # 8. recompute financials from components (components are the source of truth)
    df["GrossSales"] = (df["Quantity"] * df["UnitPrice"]).round(2)
    df["DiscountAmount"] = (df["GrossSales"] * df["DiscountPct"]).round(2)
    df["SalesAmount"] = (df["GrossSales"] - df["DiscountAmount"]).round(2)
    df["CostAmount"] = (df["Quantity"] * df["UnitCost"]).round(2)
    df["Profit"] = (df["SalesAmount"] - df["CostAmount"]).round(2)
    bad_total = (df["ReportedLineTotal"] - df["SalesAmount"]).abs() > 0.005
    log.add("recompute_line_totals", bad_total.sum(),
            "Reported Line Total did not equal Qty x Price x (1 - Discount); replaced by recomputed net sales "
            f"(overstatement removed: ${(df.loc[bad_total, 'ReportedLineTotal'] - df.loc[bad_total, 'SalesAmount']).sum():,.2f})")
    return df


def build_dim_date() -> pd.DataFrame:
    d = pd.DataFrame({"Date": pd.date_range(CALENDAR_START, CALENDAR_END, freq="D")})
    d["DateKey"] = d["Date"].dt.strftime("%Y%m%d").astype(int)
    d["Year"] = d["Date"].dt.year
    d["QuarterNumber"] = d["Date"].dt.quarter
    d["Quarter"] = "Q" + d["QuarterNumber"].astype(str)
    d["YearQuarter"] = d["Year"].astype(str) + "-" + d["Quarter"]
    d["YearQuarterNumber"] = d["Year"] * 10 + d["QuarterNumber"]
    d["MonthNumber"] = d["Date"].dt.month
    d["MonthName"] = d["Date"].dt.strftime("%B")
    d["MonthShort"] = d["Date"].dt.strftime("%b")
    d["YearMonth"] = d["Date"].dt.strftime("%Y-%m")
    d["YearMonthNumber"] = d["Year"] * 100 + d["MonthNumber"]
    d["MonthStartDate"] = d["Date"].values.astype("datetime64[M]")
    d["DayOfMonth"] = d["Date"].dt.day
    d["DayOfWeekNumber"] = d["Date"].dt.dayofweek + 1
    d["DayOfWeek"] = d["Date"].dt.strftime("%A")
    d["IsWeekend"] = d["DayOfWeekNumber"] >= 6
    return d


def price_band(p: float) -> tuple[str, int]:
    if p < 50:
        return "Under $50", 1
    if p < 200:
        return "$50-$199", 2
    if p < 500:
        return "$200-$499", 3
    return "$500+", 4


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", default=str(ROOT / "data" / "raw"))
    ap.add_argument("--out-dir", default=str(ROOT / "data" / "processed"))
    args = ap.parse_args()
    raw_dir, out = Path(args.raw_dir), Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    log = CleaningLog()
    print("Cleaning log:")

    # ---------------- masters ----------------
    products = pd.read_csv(raw_dir / "product_master.csv")
    for c in ["ProductID", "ProductName", "Category", "Subcategory", "Brand"]:
        products[c] = canon_text(products[c])
    assert products["ProductID"].is_unique and products["ProductName"].is_unique
    customers = pd.read_csv(raw_dir / "customer_master.csv", dtype={"CustomerID": str})
    geo_ref = pd.read_csv(raw_dir / "geography_reference.csv")

    orders = clean_orders(raw_dir, log, products)

    # ---------------- dimensions ----------------
    dim_channel = pd.DataFrame(CHANNEL_DIM, columns=["ChannelKey", "ChannelCode", "ChannelName", "ChannelType"])

    geo = geo_ref.copy()
    geo["Country"] = "United States"
    geo = geo.sort_values(["Region", "State", "City"]).reset_index(drop=True)
    geo["GeographyKey"] = np.arange(1, len(geo) + 1)
    dim_geo = geo[columns("DimGeography")]

    prod = products.sort_values("ProductID").reset_index(drop=True)
    prod["ProductKey"] = np.arange(1, len(prod) + 1)
    bands = prod["ListPrice"].map(price_band)
    prod["PriceBand"] = bands.map(lambda b: b[0])
    prod["PriceBandOrder"] = bands.map(lambda b: b[1])
    dim_product = prod[columns("DimProduct")]

    cust = customers.sort_values("CustomerID").reset_index(drop=True)
    cust["CustomerKey"] = np.arange(1, len(cust) + 1)
    cust["CustomerSince"] = pd.to_datetime(cust["CustomerSince"])

    # ---------------- fact ----------------
    f = orders.merge(cust[["CustomerID", "CustomerKey", "City", "State"]], left_on="Customer ID",
                     right_on="CustomerID", how="left", validate="many_to_one", suffixes=("", "_m"))
    if f["CustomerKey"].isna().any():
        raise ValueError("Order lines reference unknown customers")
    # ship-to location comes from the order; it must exist in the geography reference
    f = f.merge(dim_geo[["GeographyKey", "City", "State", "Region"]], on=["City", "State"], how="left",
                suffixes=("", "_geo"), validate="many_to_one")
    if f["GeographyKey"].isna().any():
        raise ValueError("Order lines reference unknown cities")
    if (f["Region"] != f["Region_geo"]).any():
        raise ValueError("Region on order disagrees with geography reference")
    f = f.merge(prod[["ProductID", "ProductKey"]], left_on="Product ID", right_on="ProductID", how="left")
    f = f.merge(dim_channel[["ChannelKey", "ChannelName"]], left_on="Sales Channel", right_on="ChannelName", how="left")

    f = f.sort_values(["OrderDate", "Order ID", "OrderLineNumber"]).reset_index(drop=True)
    f["SalesLineID"] = np.arange(1, len(f) + 1)
    f["OrderID"] = f["Order ID"]
    f["OrderStatus"] = f["Order Status"]
    f["DiscountBandOrder"] = np.select([f["DiscountPct"] == 0, f["DiscountPct"] <= 0.10, f["DiscountPct"] <= 0.20,
                                        f["DiscountPct"] <= 0.30], [1, 2, 3, 4], 5)
    f["DiscountBand"] = f["DiscountBandOrder"].map({1: "No discount", 2: "1-10%", 3: "11-20%", 4: "21-30%", 5: "31-40%"})
    if (f["DiscountPct"] > 0.40).any():
        raise ValueError("Discount above 40% found; extend DiscountBand rules")
    f["DaysToShip"] = (f["ShipDate"] - f["OrderDate"]).dt.days.astype("Int64")

    # order-level attributes must be identical on every line of an order
    per_order = f.groupby("OrderID")[["OrderDate", "CustomerKey", "ChannelKey", "GeographyKey"]].nunique()
    if (per_order > 1).any().any():
        raise ValueError("Order-level attributes vary within an order")
    fact = f[columns("FactSales")].copy()

    # ---------------- customer enrichment (static, as of extract date) ----------------
    cs = fact.groupby("CustomerKey").agg(FirstOrderDate=("OrderDate", "min"), LastOrderDate=("OrderDate", "max"),
                                         LifetimeOrders=("OrderID", "nunique"), LifetimeSales=("SalesAmount", "sum"))
    cust = cust.merge(cs, left_on="CustomerKey", right_index=True, how="left")
    cust["LifetimeOrders"] = cust["LifetimeOrders"].fillna(0).astype(int)
    cust["LifetimeSales"] = cust["LifetimeSales"].fillna(0).round(2)
    buyers = cust["LifetimeOrders"] > 0
    pct_rank = cust.loc[buyers, "LifetimeSales"].rank(ascending=False, method="first") / buyers.sum()
    cust["ValueTier"], cust["ValueTierOrder"] = "No purchases", 4
    cust.loc[buyers, "ValueTier"] = np.select([pct_rank <= 0.10, pct_rank <= 0.30],
                                              ["A - Top 10%", "B - Next 20%"], "C - Remaining 70%")
    cust.loc[buyers, "ValueTierOrder"] = np.select([pct_rank <= 0.10, pct_rank <= 0.30], [1, 2], 3)
    o = cust["LifetimeOrders"]
    cust["PurchaseFrequency"] = np.select([o == 0, o == 1, o <= 3, o <= 9],
                                          ["No purchases", "One-time (1)", "Occasional (2-3)", "Repeat (4-9)"],
                                          "Frequent (10+)")
    cust["PurchaseFrequencyOrder"] = np.select([o == 0, o == 1, o <= 3, o <= 9], [5, 1, 2, 3], 4)
    log.add("customers_without_orders", (~buyers).sum(),
            "Customers in the CRM with no 2023-2025 orders kept in DimCustomer (ValueTier = 'No purchases')")
    dim_customer = cust[columns("DimCustomer")]

    # ---------------- targets ----------------
    t = pd.read_excel(raw_dir / "sales_targets_2023_2025.xlsx", sheet_name="Targets")
    log.add("load_targets", len(t), "Finance target rows loaded from Excel")
    bad_t_reg = ~t["Region"].isin(set(REGION_MAP.values()))
    t["Region"] = canon_text(t["Region"]).str.lower().map(REGION_MAP)
    log.add("standardise_target_regions", bad_t_reg.sum(), "Legacy region spelling 'Mid-West' mapped to 'Midwest'")
    t["TargetMonth"] = pd.to_datetime(t["Fiscal Year"].astype(str) + "-" + t["Month"], format="%Y-%b")
    t = t.merge(dim_channel[["ChannelKey", "ChannelName"]], left_on="Channel", right_on="ChannelName", how="left")
    if t[["Region", "ChannelKey"]].isna().any().any():
        raise ValueError("Unmapped target attributes")
    t = t.rename(columns={"Target (USD)": "TargetAmount"})
    t = t.sort_values(["TargetMonth", "Region", "Category", "ChannelKey"]).reset_index(drop=True)
    t["TargetID"] = np.arange(1, len(t) + 1)
    fact_target = t[columns("FactSalesTarget")]

    dim_date = build_dim_date()

    # ---------------- write ----------------
    tables = {"FactSales": fact, "FactSalesTarget": fact_target, "DimDate": dim_date, "DimProduct": dim_product,
              "DimCustomer": dim_customer, "DimGeography": dim_geo, "DimSalesChannel": dim_channel}
    for name, tbl in tables.items():
        tbl = tbl.copy()
        for c in tbl.columns:
            if pd.api.types.is_datetime64_any_dtype(tbl[c]):
                tbl[c] = tbl[c].dt.strftime("%Y-%m-%d")
        for c in tbl.columns:
            if pd.api.types.is_bool_dtype(tbl[c]):
                tbl[c] = tbl[c].map({True: "true", False: "false"})
        tbl.to_csv(out / f"{name}.csv", index=False, float_format="%.4f" if name == "DimGeography" else None)
    log.add("write_outputs", len(fact), f"Fact rows written; tables: {', '.join(tables)}")

    summary = {name: int(len(tbl)) for name, tbl in tables.items()}
    (out / "cleaning_log.json").write_text(json.dumps({"row_counts": summary, "steps": log.steps}, indent=2))
    print("Row counts:", summary)


if __name__ == "__main__":
    main()
