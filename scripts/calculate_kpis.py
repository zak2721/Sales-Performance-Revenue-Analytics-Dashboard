"""
Independently calculate the report's KPIs in pandas, replicating the DAX measure logic.

Purpose:
  1. Provide expected values to validate the Power BI measures after the report is built
     (docs/kpi_reference.md lists "put this visual in this filter context -> expect this value").
  2. Supply the numbers quoted in docs/business_insights.md and the README.

Outputs: data/processed/reference_kpis.json, docs/kpi_reference.md

Usage:
    python scripts/calculate_kpis.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"


def load() -> dict[str, pd.DataFrame]:
    dates = {"FactSales": ["OrderDate", "ShipDate"], "FactSalesTarget": ["TargetMonth"],
             "DimDate": ["Date"], "DimCustomer": ["FirstOrderDate", "LastOrderDate", "CustomerSince"]}
    return {t: pd.read_csv(P / f"{t}.csv", parse_dates=dates.get(t, False))
            for t in ["FactSales", "FactSalesTarget", "DimDate", "DimProduct", "DimCustomer",
                      "DimGeography", "DimSalesChannel"]}


def kpis(f: pd.DataFrame) -> dict:
    sales, profit, gross = f["SalesAmount"].sum(), f["Profit"].sum(), f["GrossSales"].sum()
    orders, units, cost = f["OrderID"].nunique(), f["Quantity"].sum(), f["CostAmount"].sum()
    customers = f["CustomerKey"].nunique()
    disc = f["DiscountAmount"].sum()
    return {
        "Total Sales": sales, "Gross Sales": gross, "Total Orders": orders, "Total Order Lines": len(f),
        "Total Units Sold": int(units), "Total Customers": customers,
        "Average Order Value": sales / orders, "Average Selling Price": sales / units,
        "Total Cost": cost, "Total Profit": profit, "Profit Margin %": profit / sales,
        "Average Profit per Order": profit / orders, "Discount Amount": disc, "Discount Rate %": disc / gross,
        "List Margin %": (gross - cost) / gross,
    }


def r(x, nd=2):
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        return round(float(x), nd if abs(x) >= 10 else 4)
    return x


def main() -> None:
    t = load()
    f = t["FactSales"].merge(t["DimProduct"], on="ProductKey").merge(t["DimGeography"], on="GeographyKey") \
                      .merge(t["DimSalesChannel"], on="ChannelKey").merge(t["DimCustomer"], on="CustomerKey")
    f["Year"] = f["OrderDate"].dt.year
    f["YearMonth"] = f["OrderDate"].dt.strftime("%Y-%m")
    tg = t["FactSalesTarget"].merge(t["DimSalesChannel"], on="ChannelKey")
    tg["Year"] = tg["TargetMonth"].dt.year
    out: dict = {}

    out["overall"] = {k: r(v) for k, v in kpis(f).items()}
    out["overall"]["Sales Target"] = r(tg["TargetAmount"].sum())
    out["overall"]["Target Achievement %"] = r(f["SalesAmount"].sum() / tg["TargetAmount"].sum())

    # by year incl. YoY, targets, customers
    by_year = {}
    for y in sorted(f["Year"].unique()):
        fy = f[f["Year"] == y]
        k = kpis(fy)
        k["Sales Target"] = tg.loc[tg["Year"] == y, "TargetAmount"].sum()
        k["Target Achievement %"] = k["Total Sales"] / k["Sales Target"]
        k["Remaining Sales to Target"] = max(0.0, k["Sales Target"] - k["Total Sales"])
        oc = fy.groupby("CustomerKey")["OrderID"].nunique()
        k["Repeat Customers"] = int((oc >= 2).sum())
        k["Repeat Customer Rate %"] = (oc >= 2).mean()
        k["New Customers"] = int(fy.loc[fy["FirstOrderDate"].dt.year == y, "CustomerKey"].nunique())
        k["Returning Customers"] = k["Total Customers"] - k["New Customers"]
        k["Orders per Customer"] = k["Total Orders"] / k["Total Customers"]
        if y - 1 in by_year:
            p = by_year[y - 1]
            k["Sales Previous Year"] = p["Total Sales"]
            k["Sales YoY Growth %"] = k["Total Sales"] / p["Total Sales"] - 1
            k["Profit YoY Growth %"] = k["Total Profit"] / p["Total Profit"] - 1
            k["Orders YoY Growth %"] = k["Total Orders"] / p["Total Orders"] - 1
            k["AOV YoY Growth %"] = k["Average Order Value"] / p["Average Order Value"] - 1
        by_year[y] = k
    out["by_year"] = {str(y): {kk: r(vv) for kk, vv in v.items()} for y, v in by_year.items()}

    # dimension breakdowns (full period and by year)
    def breakdown(col: str, with_target: bool = False) -> dict:
        res = {}
        for key, g in f.groupby(col):
            k = kpis(g)
            row = {"Total Sales": k["Total Sales"], "Total Profit": k["Total Profit"],
                   "Profit Margin %": k["Profit Margin %"], "Discount Rate %": k["Discount Rate %"],
                   "Total Orders": k["Total Orders"], "Sales Share %": k["Total Sales"] / f["SalesAmount"].sum()}
            for y in sorted(f["Year"].unique()):
                row[f"Sales {y}"] = g.loc[g["Year"] == y, "SalesAmount"].sum()
            if with_target:
                tcol = {"Region": "Region", "Category": "Category", "ChannelName": "ChannelName"}[col]
                for y in sorted(f["Year"].unique()):
                    tv = tg.loc[(tg[tcol] == key) & (tg["Year"] == y), "TargetAmount"].sum()
                    row[f"Target Achievement % {y}"] = row[f"Sales {y}"] / tv
            res[str(key)] = {kk: r(vv) for kk, vv in row.items()}
        return res

    out["by_region"] = breakdown("Region", True)
    out["by_category"] = breakdown("Category", True)
    out["by_channel"] = breakdown("ChannelName", True)
    out["by_subcategory"] = breakdown("Subcategory")
    out["by_segment"] = breakdown("Segment")
    out["by_discount_band"] = breakdown("DiscountBand")
    out["by_state_top5"] = dict(sorted(breakdown("State").items(), key=lambda kv: -kv[1]["Total Sales"])[:5])

    # products
    prod = f.groupby("ProductName").agg(Sales=("SalesAmount", "sum"), Profit=("Profit", "sum"),
                                        Gross=("GrossSales", "sum"), Disc=("DiscountAmount", "sum"),
                                        Subcategory=("Subcategory", "first"))
    prod["Margin"] = prod["Profit"] / prod["Sales"]
    prod["DiscountRate"] = prod["Disc"] / prod["Gross"]
    total = f["SalesAmount"].sum()
    top10 = prod.sort_values("Sales", ascending=False).head(10)
    out["top10_products"] = [{"Product": i, "Subcategory": row.Subcategory, "Sales": r(row.Sales),
                              "Profit Margin %": r(row.Margin), "Contribution %": r(row.Sales / total)}
                             for i, row in top10.iterrows()]
    out["bottom5_products_by_profit"] = [{"Product": i, "Sales": r(row.Sales), "Profit": r(row.Profit),
                                          "Profit Margin %": r(row.Margin)}
                                         for i, row in prod.sort_values("Profit").head(5).iterrows()]
    out["lowest_margin_products"] = [{"Product": i, "Sales": r(row.Sales), "Profit Margin %": r(row.Margin),
                                      "Discount Rate %": r(row.DiscountRate)}
                                     for i, row in prod.sort_values("Margin").head(5).iterrows()]
    out["top10_products_sales_share"] = r(top10["Sales"].sum() / total)
    out["products_with_negative_profit"] = int((prod["Profit"] < 0).sum())
    out["product_discount_margin_correlation"] = r(prod["DiscountRate"].corr(prod["Margin"]))

    # customers
    cust = f.groupby(["CustomerKey", "CustomerName", "Segment"])["SalesAmount"].sum().sort_values(ascending=False)
    n_top = int(np.ceil(len(cust) * 0.2))
    out["customers"] = {
        "Total Customers": int(len(cust)),
        "Top 10 Customers Sales Share %": r(cust.head(10).sum() / total),
        "Top 20% Customers Sales Share %": r(cust.head(n_top).sum() / total),
        "Repeat Customers (2023-2025)": int((f.groupby("CustomerKey")["OrderID"].nunique() >= 2).sum()),
        "Repeat Customer Rate % (2023-2025)": r((f.groupby("CustomerKey")["OrderID"].nunique() >= 2).mean()),
        "Customers in DimCustomer with no orders": int((t["DimCustomer"]["LifetimeOrders"] == 0).sum()),
        "top5": [{"Customer": k[1], "Segment": k[2], "Sales": r(v), "Contribution %": r(v / total)}
                 for k, v in cust.head(5).items()],
        "value_tier": {k: r(v) for k, v in
                       f.groupby("ValueTier")["SalesAmount"].sum().div(total).items()},
        "value_tier_customers": {k: int(v) for k, v in t["DimCustomer"]["ValueTier"].value_counts().items()},
        "purchase_frequency_customers": {k: int(v) for k, v in
                                         t["DimCustomer"]["PurchaseFrequency"].value_counts().items()},
    }

    # profitability / discount
    full = f[f["DiscountPct"] == 0]
    dsc = f[f["DiscountPct"] > 0]
    loss = f[f["Profit"] < 0]
    out["profitability"] = {
        "Discounted Sales Share %": r(dsc["SalesAmount"].sum() / total),
        "Profit Margin % (Full-Price Lines)": r(full["Profit"].sum() / full["SalesAmount"].sum()),
        "Profit Margin % (Discounted Lines)": r(dsc["Profit"].sum() / dsc["SalesAmount"].sum()),
        "Margin Erosion from Discounts": r(out["overall"]["List Margin %"] - out["overall"]["Profit Margin %"]),
        "Loss-Making Lines": int(len(loss)),
        "Loss-Making Sales": r(loss["SalesAmount"].sum()),
        "Loss on Loss-Making Lines": r(loss["Profit"].sum()),
        "Loss-making lines by subcategory": {k: int(v) for k, v in
                                             loss["Subcategory"].value_counts().head(5).items()},
    }

    # time: monthly, MoM, rolling, YTD, seasonality, ops
    m = f.groupby("YearMonth")["SalesAmount"].sum()
    out["monthly_sales"] = {k: r(v) for k, v in m.items()}
    out["time"] = {
        "Sales Dec 2025": r(m["2025-12"]),
        "Sales Previous Month (Dec 2025 context)": r(m["2025-11"]),
        "Sales MoM Growth % (Dec 2025)": r(m["2025-12"] / m["2025-11"] - 1),
        "Sales Rolling 3M Avg (Dec 2025)": r(m[["2025-10", "2025-11", "2025-12"]].mean()),
        "Sales YTD at Jun 2025": r(m[[f"2025-{i:02d}" for i in range(1, 7)]].sum()),
        "Sales PYTD at Jun 2025": r(m[[f"2024-{i:02d}" for i in range(1, 7)]].sum()),
        "Profit YTD 2025 (full year)": r(f.loc[f["Year"] == 2025, "Profit"].sum()),
    }
    mon = f.groupby([f["Year"], f["OrderDate"].dt.month])["SalesAmount"].sum().unstack(0)
    share = mon / mon.sum()
    out["seasonality"] = {
        "monthly share of annual sales by year": {str(y): {int(mm): r(v) for mm, v in share[y].items()} for y in share},
        "Q4 share by year": {str(y): r(share[y].loc[10:12].sum()) for y in share},
        "Nov+Dec share by year": {str(y): r(share[y].loc[11:12].sum()) for y in share},
    }
    shipped = f[f["OrderStatus"] == "Shipped"].groupby(["OrderID", "ChannelName"])["DaysToShip"].max().reset_index()
    out["operations"] = {
        "Open Orders": int(f.loc[f["OrderStatus"] == "Open", "OrderID"].nunique()),
        "Average Days to Ship": r(shipped["DaysToShip"].mean()),
        "Average Days to Ship by channel": {k: r(v) for k, v in shipped.groupby("ChannelName")["DaysToShip"].mean().items()},
    }

    (P / "reference_kpis.json").write_text(json.dumps(out, indent=2))
    write_markdown(out)
    print("Wrote data/processed/reference_kpis.json and docs/kpi_reference.md")


def money(x):
    return f"-${abs(x):,.0f}" if x < 0 else f"${x:,.0f}"


def pct(x):
    return f"{x * 100:.1f}%"


def write_markdown(o: dict) -> None:
    ov = o["overall"]
    L = ["# KPI Reference Values",
         "",
         "_Generated by `scripts/calculate_kpis.py` from `data/processed/` (synthetic data, seed 42). "
         "These values are calculated independently in pandas using the same definitions as the DAX measures. "
         "Use them to validate the Power BI report: build the visual/context listed and compare. "
         "Differences larger than rounding indicate a model or measure problem._",
         "",
         "## 1. Whole dataset (no filters, Jan 2023 - Dec 2025)",
         "",
         "| Measure | Expected value |",
         "|---|---|"]
    fmt = {"%": pct, "$": money}
    for k, v in ov.items():
        if k.endswith("%"):
            L.append(f"| {k} | {pct(v)} |")
        elif k in ("Total Orders", "Total Order Lines", "Total Units Sold", "Total Customers"):
            L.append(f"| {k} | {v:,} |")
        elif k in ("Average Order Value", "Average Selling Price", "Average Profit per Order"):
            L.append(f"| {k} | ${v:,.2f} |")
        else:
            L.append(f"| {k} | {money(v)} |")
    L += ["", "## 2. By year (matrix rows = DimDate[Year])", "",
          "| Measure | 2023 | 2024 | 2025 |", "|---|---|---|---|"]
    rows = ["Total Sales", "Total Profit", "Profit Margin %", "Total Orders", "Total Customers",
            "Average Order Value", "Discount Rate %", "Sales Target", "Target Achievement %",
            "Remaining Sales to Target", "Sales YoY Growth %", "Profit YoY Growth %", "Orders YoY Growth %",
            "AOV YoY Growth %", "New Customers", "Returning Customers", "Repeat Customers", "Repeat Customer Rate %"]
    for k in rows:
        cells = []
        for y in ("2023", "2024", "2025"):
            v = o["by_year"][y].get(k)
            if v is None:
                cells.append("(blank)")
            elif k.endswith("%"):
                cells.append(pct(v))
            elif k in ("Total Orders", "Total Customers", "New Customers", "Returning Customers", "Repeat Customers"):
                cells.append(f"{v:,}")
            elif k == "Average Order Value":
                cells.append(f"${v:,.2f}")
            else:
                cells.append(money(v))
        L.append(f"| {k} | " + " | ".join(cells) + " |")
    L += ["", "_YoY measures are blank for 2023 because the dataset has no 2022 data._", ""]

    for title, key, tgt in [("Region (DimGeography[Region])", "by_region", True),
                            ("Category (DimProduct[Category])", "by_category", True),
                            ("Channel (DimSalesChannel[ChannelName])", "by_channel", True),
                            ("Customer segment (DimCustomer[Segment])", "by_segment", False),
                            ("Discount band (FactSales[DiscountBand])", "by_discount_band", False)]:
        L += [f"## {title}", ""]
        hdr = "| Value | Sales | Share | Profit | Margin | Discount rate | Sales 2023 | Sales 2024 | Sales 2025 |"
        sep = "|---|---|---|---|---|---|---|---|---|"
        if tgt:
            hdr += " Target ach. 2023 | 2024 | 2025 |"
            sep += "---|---|---|"
        L += [hdr, sep]
        for name, v in sorted(o[key].items(), key=lambda kv: -kv[1]["Total Sales"]):
            line = (f"| {name} | {money(v['Total Sales'])} | {pct(v['Sales Share %'])} | {money(v['Total Profit'])} | "
                    f"{pct(v['Profit Margin %'])} | {pct(v['Discount Rate %'])} | {money(v['Sales 2023'])} | "
                    f"{money(v['Sales 2024'])} | {money(v['Sales 2025'])} |")
            if tgt:
                line += " " + " | ".join(pct(v[f"Target Achievement % {y}"]) for y in (2023, 2024, 2025)) + " |"
            L.append(line)
        L.append("")

    L += ["## Subcategory (sorted by margin)", "", "| Subcategory | Sales | Share | Margin | Discount rate |",
          "|---|---|---|---|---|"]
    for name, v in sorted(o["by_subcategory"].items(), key=lambda kv: kv[1]["Profit Margin %"]):
        L.append(f"| {name} | {money(v['Total Sales'])} | {pct(v['Sales Share %'])} | {pct(v['Profit Margin %'])} | "
                 f"{pct(v['Discount Rate %'])} |")
    L += ["", "## Top 10 products by sales (whole dataset)", "",
          "| Rank | Product | Subcategory | Sales | Margin | Contribution |", "|---|---|---|---|---|---|"]
    for i, p in enumerate(o["top10_products"], 1):
        L.append(f"| {i} | {p['Product']} | {p['Subcategory']} | {money(p['Sales'])} | {pct(p['Profit Margin %'])} | "
                 f"{pct(p['Contribution %'])} |")
    L += ["", f"Top 10 Products Sales Share %: **{pct(o['top10_products_sales_share'])}**  ",
          f"Products with Negative Profit: **{o['products_with_negative_profit']}**", "",
          "## Lowest-margin products", "", "| Product | Sales | Margin | Discount rate |", "|---|---|---|---|"]
    for p in o["lowest_margin_products"]:
        L.append(f"| {p['Product']} | {money(p['Sales'])} | {pct(p['Profit Margin %'])} | {pct(p['Discount Rate %'])} |")
    c = o["customers"]
    L += ["", "## Customers (whole dataset)", "", "| Measure | Expected |", "|---|---|",
          f"| Total Customers | {c['Total Customers']:,} |",
          f"| Top 10 Customers Sales Share % | {pct(c['Top 10 Customers Sales Share %'])} |",
          f"| Top 20% Customers Sales Share % | {pct(c['Top 20% Customers Sales Share %'])} |",
          f"| Repeat Customers | {c['Repeat Customers (2023-2025)']:,} |",
          f"| Repeat Customer Rate % | {pct(c['Repeat Customer Rate % (2023-2025)'])} |",
          f"| Top Customer by Sales | {c['top5'][0]['Customer']} ({money(c['top5'][0]['Sales'])}) |", ""]
    pr = o["profitability"]
    L += ["## Profitability and discounts (whole dataset)", "", "| Measure | Expected |", "|---|---|"]
    for k in ["Discounted Sales Share %", "Profit Margin % (Full-Price Lines)", "Profit Margin % (Discounted Lines)"]:
        L.append(f"| {k} | {pct(pr[k])} |")
    L.append(f"| Margin Erosion from Discounts | {pr['Margin Erosion from Discounts'] * 100:.1f} percentage points "
             "(Power BI shows it with a % format) |")
    L += [f"| Loss-Making Lines | {pr['Loss-Making Lines']:,} |",
          f"| Loss-Making Sales | {money(pr['Loss-Making Sales'])} |",
          f"| Loss on Loss-Making Lines | {money(pr['Loss on Loss-Making Lines'])} |", ""]
    ti = o["time"]
    L += ["## Time intelligence spot checks", "", "| Context | Measure | Expected |", "|---|---|---|",
          f"| YearMonth = 2025-12 | Total Sales | {money(ti['Sales Dec 2025'])} |",
          f"| YearMonth = 2025-12 | Sales Previous Month | {money(ti['Sales Previous Month (Dec 2025 context)'])} |",
          f"| YearMonth = 2025-12 | Sales MoM Growth % | {pct(ti['Sales MoM Growth % (Dec 2025)'])} |",
          f"| YearMonth = 2025-12 | Sales Rolling 3M Avg | {money(ti['Sales Rolling 3M Avg (Dec 2025)'])} |",
          f"| YearMonth = 2025-06 | Sales YTD | {money(ti['Sales YTD at Jun 2025'])} |",
          f"| YearMonth = 2025-06 | Sales PYTD | {money(ti['Sales PYTD at Jun 2025'])} |",
          f"| YearMonth = 2023-01 | Sales Previous Month, Sales MoM Growth % | (blank) |",
          f"| Year = 2023 | Sales YoY Growth % | (blank) |", ""]
    op = o["operations"]
    L += ["## Operations", "", f"- Open Orders: **{op['Open Orders']}**",
          f"- Average Days to Ship: **{op['Average Days to Ship']:.1f}** "
          + "(" + ", ".join(f"{k} {v:.1f}" for k, v in op["Average Days to Ship by channel"].items()) + ")", ""]
    L += ["## Target-grain checks", "",
          "- Filter DimGeography[State] = any single state: **Sales Target is blank** (targets are regional).",
          "- Filter DimProduct[Subcategory] = Laptops: **Sales Target is blank** (targets are by category).",
          "- Filter DimProduct[Category] = Electronics: Sales Target is populated and equals the Electronics row above.",
          "- Filter DimCustomer[Segment] = Corporate: **Sales Target is blank** (no customer-level targets).", ""]
    (ROOT / "docs" / "kpi_reference.md").write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
