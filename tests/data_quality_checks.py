"""
Automated data-quality and model-consistency checks.

Run directly (no extra dependencies):
    python tests/data_quality_checks.py
or with pytest if installed:
    pytest tests/data_quality_checks.py

Each check_* function raises AssertionError with a clear message on failure.
What is NOT covered here (needs Power BI Desktop): DAX execution, visuals, interactions.
Those are listed as manual checks in docs/testing_and_validation.md.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"
sys.path.insert(0, str(ROOT / "scripts"))
from measures import MEASURES  # noqa: E402
from schema import SCHEMA, columns  # noqa: E402

TOL = 0.005  # half a cent
_cache: dict[str, pd.DataFrame] = {}


def tbl(name: str) -> pd.DataFrame:
    if name not in _cache:
        date_cols = [c[0] for c in SCHEMA[name]["columns"] if c[1] == "type date"]
        _cache[name] = pd.read_csv(P / f"{name}.csv", parse_dates=date_cols, keep_default_na=True)
    return _cache[name]


# ----------------------------------------------------------------------------- structure
def check_files_match_schema():
    for t in SCHEMA:
        cols = list(pd.read_csv(P / f"{t}.csv", nrows=0).columns)
        assert cols == columns(t), f"{t}: columns {cols} != schema {columns(t)}"
        assert len(tbl(t)) > 0, f"{t} is empty"


def check_primary_keys_unique():
    keys = {"FactSales": ["SalesLineID"], "FactSalesTarget": ["TargetID"], "DimDate": ["Date"],
            "DimProduct": ["ProductKey"], "DimCustomer": ["CustomerKey"], "DimGeography": ["GeographyKey"],
            "DimSalesChannel": ["ChannelKey"]}
    for t, k in keys.items():
        assert not tbl(t).duplicated(k).any(), f"{t}: duplicate primary key {k}"
    assert not tbl("FactSales").duplicated(["OrderID", "OrderLineNumber"]).any(), "Duplicate OrderID+line"
    for t, k in [("DimProduct", "ProductID"), ("DimProduct", "ProductName"), ("DimCustomer", "CustomerID"),
                 ("DimSalesChannel", "ChannelName")]:
        assert tbl(t)[k].is_unique, f"{t}[{k}] not unique (needed for Top N and drill-through)"
    assert not tbl("FactSalesTarget").duplicated(["TargetMonth", "Region", "Category", "ChannelKey"]).any(), \
        "Duplicate target grain rows"


def check_no_unexpected_nulls():
    allowed = {("FactSales", "ShipDate"), ("FactSales", "DaysToShip"),
               ("DimCustomer", "FirstOrderDate"), ("DimCustomer", "LastOrderDate")}
    for t in SCHEMA:
        nulls = tbl(t).isna().sum()
        bad = {c: int(n) for c, n in nulls.items() if n and (t, c) not in allowed}
        assert not bad, f"{t}: unexpected nulls {bad}"
    f = tbl("FactSales")
    assert (f["ShipDate"].isna() == (f["OrderStatus"] == "Open")).all(), "Ship date blank iff order is Open"
    c = tbl("DimCustomer")
    assert (c["FirstOrderDate"].isna() == (c["LifetimeOrders"] == 0)).all(), "FirstOrderDate blank iff no orders"


# ----------------------------------------------------------------------------- relationships
def check_referential_integrity():
    f = tbl("FactSales")
    for fk, dim, pk in [("CustomerKey", "DimCustomer", "CustomerKey"), ("ProductKey", "DimProduct", "ProductKey"),
                        ("GeographyKey", "DimGeography", "GeographyKey"), ("ChannelKey", "DimSalesChannel", "ChannelKey")]:
        missing = set(f[fk]) - set(tbl(dim)[pk])
        assert not missing, f"FactSales[{fk}] has {len(missing)} keys missing in {dim}"
    dates = set(tbl("DimDate")["Date"])
    assert set(f["OrderDate"]) <= dates, "OrderDate outside DimDate"
    assert set(f["ShipDate"].dropna()) <= dates, "ShipDate outside DimDate (inactive relationship would break)"
    t = tbl("FactSalesTarget")
    assert set(t["TargetMonth"]) <= dates, "TargetMonth outside DimDate"
    assert (t["TargetMonth"].dt.day == 1).all(), "TargetMonth must be the first day of the month"
    assert set(t["ChannelKey"]) <= set(tbl("DimSalesChannel")["ChannelKey"]), "Target channel unknown"
    assert set(t["Region"]) == set(tbl("DimGeography")["Region"]), "Target regions must match DimGeography[Region] (TREATAS)"
    assert set(t["Category"]) == set(tbl("DimProduct")["Category"]), "Target categories must match DimProduct[Category] (TREATAS)"


def check_order_level_consistency():
    per = tbl("FactSales").groupby("OrderID")[["OrderDate", "CustomerKey", "ChannelKey", "GeographyKey",
                                                "OrderStatus"]].nunique()
    assert (per <= 1).all().all(), "Order header attributes differ between lines of the same order"


def check_hierarchies_consistent():
    p = tbl("DimProduct")
    assert (p.groupby("Subcategory")["Category"].nunique() == 1).all(), "Subcategory maps to >1 category"
    g = tbl("DimGeography")
    assert (g.groupby("State")["Region"].nunique() == 1).all(), "State maps to >1 region"
    assert not g.duplicated(["City", "State"]).any(), "Duplicate city/state"
    assert g["Latitude"].between(24, 50).all() and g["Longitude"].between(-125, -66).all(), "Coordinates outside contiguous US"
    assert set(tbl("DimCustomer")["Segment"]) == {"Consumer", "Small Business", "Corporate"}


# ----------------------------------------------------------------------------- dates
def check_date_table():
    d = tbl("DimDate")
    rng = pd.date_range("2023-01-01", "2025-12-31", freq="D")
    assert len(d) == len(rng) and (d["Date"].values == rng.values).all(), "DimDate must be contiguous full years 2023-2025"
    assert (d["DateKey"] == d["Date"].dt.strftime("%Y%m%d").astype(int)).all()
    assert (d["YearMonthNumber"] == d["Year"] * 100 + d["MonthNumber"]).all()
    assert d.groupby("YearMonth")["YearMonthNumber"].nunique().eq(1).all(), "YearMonth sort key not 1:1"
    assert d.groupby("MonthName")["MonthNumber"].nunique().eq(1).all(), "MonthName sort key not 1:1"
    assert d.groupby("Quarter")["QuarterNumber"].nunique().eq(1).all()
    assert (d["IsWeekend"] == (d["Date"].dt.dayofweek >= 5)).all()


def check_valid_dates():
    f = tbl("FactSales")
    shipped = f.dropna(subset=["ShipDate"])
    assert (shipped["ShipDate"] >= shipped["OrderDate"]).all(), "Ship date before order date"
    assert (shipped["DaysToShip"] == (shipped["ShipDate"] - shipped["OrderDate"]).dt.days).all(), "DaysToShip wrong"
    assert shipped["DaysToShip"].between(0, 30).all(), "Implausible shipping time"
    assert f["OrderDate"].max() <= pd.Timestamp("2025-12-31")
    c = tbl("DimCustomer").dropna(subset=["FirstOrderDate"])
    assert (c["FirstOrderDate"] <= c["LastOrderDate"]).all()


# ----------------------------------------------------------------------------- financials
def check_financial_reconciliation():
    f = tbl("FactSales")
    assert (f["Quantity"] > 0).all() and (f["UnitPrice"] > 0).all() and (f["UnitCost"] > 0).all()
    assert f["DiscountPct"].between(0, 0.40).all(), "Discount outside 0-40%"
    checks = {
        "GrossSales = Quantity x UnitPrice": f["Quantity"] * f["UnitPrice"] - f["GrossSales"],
        "DiscountAmount = GrossSales x DiscountPct": f["GrossSales"] * f["DiscountPct"] - f["DiscountAmount"],
        "SalesAmount = GrossSales - DiscountAmount": f["GrossSales"] - f["DiscountAmount"] - f["SalesAmount"],
        "CostAmount = Quantity x UnitCost": f["Quantity"] * f["UnitCost"] - f["CostAmount"],
        "Profit = SalesAmount - CostAmount": f["SalesAmount"] - f["CostAmount"] - f["Profit"],
    }
    for name, diff in checks.items():
        assert (diff.abs() <= TOL + 1e-9).all(), f"{name}: {(diff.abs() > TOL).sum()} rows off by > half a cent"
    band_ok = f.groupby("DiscountBand")["DiscountPct"].agg(["min", "max"])
    assert band_ok.loc["No discount", "max"] == 0
    assert f.groupby("DiscountBand")["DiscountBandOrder"].nunique().eq(1).all()


def check_aggregates_reconcile():
    f = tbl("FactSales")
    total = f["SalesAmount"].sum()
    for dim_key, dim, attr in [("GeographyKey", "DimGeography", "Region"), ("ProductKey", "DimProduct", "Category"),
                               ("ChannelKey", "DimSalesChannel", "ChannelName"), ("CustomerKey", "DimCustomer", "Segment")]:
        by = f.merge(tbl(dim)[[dim_key, attr]], on=dim_key).groupby(attr)["SalesAmount"].sum().sum()
        assert abs(by - total) < 0.01, f"Sales by {attr} ({by:,.2f}) != total ({total:,.2f})"
    by_year = f.groupby(f["OrderDate"].dt.year)["SalesAmount"].sum().sum()
    assert abs(by_year - total) < 0.01
    # gross - discount = net and net - cost = profit at total level
    assert abs(f["GrossSales"].sum() - f["DiscountAmount"].sum() - total) < 1.0
    assert abs(total - f["CostAmount"].sum() - f["Profit"].sum()) < 1.0
    # customer enrichment agrees with the fact
    c = tbl("DimCustomer").set_index("CustomerKey")
    s = f.groupby("CustomerKey")["SalesAmount"].sum()
    assert ((c.loc[s.index, "LifetimeSales"] - s).abs() < 0.01).all(), "DimCustomer[LifetimeSales] disagrees with fact"
    o = f.groupby("CustomerKey")["OrderID"].nunique()
    assert (c.loc[o.index, "LifetimeOrders"] == o).all(), "DimCustomer[LifetimeOrders] disagrees with fact"


def check_reference_kpis_match_fact():
    ref = json.loads((P / "reference_kpis.json").read_text())
    f = tbl("FactSales")
    assert abs(ref["overall"]["Total Sales"] - f["SalesAmount"].sum()) < 0.01
    assert abs(ref["overall"]["Total Profit"] - f["Profit"].sum()) < 0.01
    assert ref["overall"]["Total Orders"] == f["OrderID"].nunique()
    # ratio of sums, not average of ratios
    assert abs(ref["overall"]["Profit Margin %"] - f["Profit"].sum() / f["SalesAmount"].sum()) < 1e-4
    ys = ref["by_year"]
    for y in ("2024", "2025"):
        expected = ys[y]["Total Sales"] / ys[str(int(y) - 1)]["Total Sales"] - 1
        assert abs(ys[y]["Sales YoY Growth %"] - expected) < 1e-3
    assert "Sales YoY Growth %" not in ys["2023"], "2023 YoY must be blank (no 2022 data)"


# ----------------------------------------------------------------------------- targets
def check_targets():
    t = tbl("FactSalesTarget")
    assert (t["TargetAmount"] > 0).all(), "Non-positive target"
    months = t["TargetMonth"].dt.to_period("M").nunique()
    grid = months * t["Region"].nunique() * t["Category"].nunique() * t["ChannelKey"].nunique()
    assert len(t) == grid, f"Target grid incomplete: {len(t)} rows vs {grid}"
    sales_months = set(tbl("FactSales")["OrderDate"].dt.to_period("M"))
    assert set(t["TargetMonth"].dt.to_period("M")) == sales_months, "Targets and sales cover different months"
    # targets reconcile to the raw finance workbook
    raw = pd.read_excel(RAW / "sales_targets_2023_2025.xlsx", sheet_name="Targets")
    assert abs(raw["Target (USD)"].sum() - t["TargetAmount"].sum()) < 0.01, "Targets lost or duplicated in cleaning"


# ----------------------------------------------------------------------------- cleaning
def check_cleaning_log():
    log = json.loads((P / "cleaning_log.json").read_text())
    steps = {s["step"]: s["rows_affected"] for s in log["steps"]}
    raw_rows = steps["load"]
    expected = raw_rows - steps["remove_exact_duplicates"] - steps["remove_test_accounts"]
    assert expected == len(tbl("FactSales")), "Raw rows - removed rows != fact rows"
    assert log["row_counts"]["FactSales"] == len(tbl("FactSales"))
    f = tbl("FactSales")
    assert f["OrderID"].str.match(r"^SO-\d{4}-\d{6}$").all(), "Test or malformed order IDs remain"


def check_text_conformed():
    for t in SCHEMA:
        df = tbl(t)
        for c in [c for c in df.columns if pd.api.types.is_string_dtype(df[c]) or df[c].dtype == object]:
            s = df[c].dropna().astype(str)
            assert (s == s.str.strip()).all(), f"{t}[{c}] has leading/trailing spaces"
    assert set(tbl("DimProduct")["Category"]) == {"Electronics", "Furniture", "Office Supplies", "Home & Kitchen"}
    assert set(tbl("DimGeography")["Region"]) == {"Northeast", "Midwest", "South", "West"}
    assert len(tbl("DimSalesChannel")) == 4


# ----------------------------------------------------------------------------- DAX / docs consistency
def check_dax_references_exist():
    """Static lint: every Table[Column] and [Measure] referenced in a DAX measure exists."""
    cols = {(t, c[0]) for t in SCHEMA for c in SCHEMA[t]["columns"]}
    names = {m[0] for m in MEASURES}
    assert len(names) == len(MEASURES), "Duplicate measure names"
    for name, _, _, _, expr in MEASURES:
        code = re.sub(r'"[^"]*"', '""', expr)  # ignore string literals
        for t, c in re.findall(r"\b([A-Za-z_]+)\[([^\]]+)\]", code):
            assert (t, c) in cols, f"[{name}] references unknown column {t}[{c}]"
        for t in re.findall(r"\(\s*([A-Za-z_]+)\s*\)", code):
            if t in SCHEMA or t.startswith(("Dim", "Fact")):
                assert t in SCHEMA, f"[{name}] references unknown table {t}"
        bare = re.sub(r"\b[A-Za-z_]+\[[^\]]+\]", "", code)
        for ref in re.findall(r"\[([^\]]+)\]", bare):
            assert ref in names, f"[{name}] references unknown measure [{ref}]"
        assert code.count("(") == code.count(")"), f"[{name}] unbalanced parentheses"


def check_generated_docs_current():
    dd = (ROOT / "docs" / "data_dictionary.md").read_text()
    for t in SCHEMA:
        for c in columns(t):
            assert f"| {c} |" in dd, f"{t}[{c}] missing from data dictionary - run build_powerbi_assets.py"
    tmdl = (ROOT / "powerbi" / "tmdl" / "measures.tmdl").read_text()
    for m in MEASURES:
        assert m[0] in tmdl, f"Measure {m[0]} missing from TMDL - run build_powerbi_assets.py"
    json.loads((ROOT / "powerbi" / "theme" / "meridian_executive_theme.json").read_text())


# ----------------------------------------------------------------------------- reproducibility
def check_reproducible_generation():
    """Regenerating with the same seed reproduces the raw data exactly."""
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_sales_data.py"), "--seed", "42",
                        "--output-dir", tmp], check=True, capture_output=True)
        for name in ["orders_export_2023_2025.csv", "product_master.csv", "customer_master.csv",
                     "geography_reference.csv"]:
            assert (Path(tmp) / name).read_bytes() == (RAW / name).read_bytes(), f"{name} differs on regeneration"
        a = pd.read_excel(Path(tmp) / "sales_targets_2023_2025.xlsx", sheet_name="Targets")
        b = pd.read_excel(RAW / "sales_targets_2023_2025.xlsx", sheet_name="Targets")
        pd.testing.assert_frame_equal(a, b)


ALL_CHECKS = [v for k, v in dict(globals()).items() if k.startswith("check_") and callable(v)]

# pytest discovery aliases
for _f in ALL_CHECKS:
    globals()["test_" + _f.__name__[len("check_"):]] = _f


def run_all(skip_slow: bool = False) -> list[tuple[str, bool, str]]:
    results = []
    for fn in ALL_CHECKS:
        if skip_slow and fn is check_reproducible_generation:
            continue
        try:
            fn()
            results.append((fn.__name__, True, (fn.__doc__ or "").strip().splitlines()[0] if fn.__doc__ else ""))
        except Exception as e:  # noqa: BLE001
            results.append((fn.__name__, False, f"{type(e).__name__}: {e}"))
    return results


if __name__ == "__main__":
    res = run_all(skip_slow="--fast" in sys.argv)
    for name, ok, msg in res:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  -> {msg}" if not ok else ""))
    failed = sum(not ok for _, ok, _ in res)
    print(f"\n{len(res) - failed}/{len(res)} checks passed")
    sys.exit(1 if failed else 0)
