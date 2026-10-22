"""
Generate Power BI build assets from the single-source definitions in schema.py and measures.py.

Outputs:
  powerbi/power_query/*.pq        Power Query (M) script per table + DataFolder parameter
  powerbi/tmdl/measures.tmdl      TMDL script that creates every measure in the _Measures table
  powerbi/dax_measures.md         Measure library documentation
  docs/data_dictionary.md         Column-level data dictionary

Usage:
    python scripts/build_powerbi_assets.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from measures import MEASURES  # noqa: E402
from schema import SCHEMA  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
NULLABLE_TEXT_TO_NULL = {"ShipDate", "DaysToShip", "FirstOrderDate", "LastOrderDate"}
LOAD_ORDER = ["DimDate", "DimProduct", "DimCustomer", "DimGeography", "DimSalesChannel", "FactSales", "FactSalesTarget"]


def tmdl_name(name: str) -> str:
    return f"'{name}'" if any(ch in name for ch in " %()-&.'") else name


def build_tmdl() -> str:
    # TMDL has no comment syntax outside /// descriptions, so usage notes live in powerbi/README.md.
    out = [
        "createOrReplace",
        "",
        "\tref table _Measures",
        "",
    ]
    for name, folder, fmt, desc, expr in MEASURES:
        out.append(f"\t\t/// {desc}")
        lines = expr.strip().splitlines()
        if len(lines) == 1:
            out.append(f"\t\tmeasure {tmdl_name(name)} = {lines[0]}")
        else:
            out.append(f"\t\tmeasure {tmdl_name(name)} =")
            out.extend(f"\t\t\t\t{ln}" for ln in lines)
        if fmt:
            out.append(f"\t\t\tformatString: {fmt}")
        out.append(f"\t\t\tdisplayFolder: {folder}")
        out.append("")
    return "\n".join(out)


def build_dax_md() -> str:
    folders: dict[str, list] = {}
    for m in MEASURES:
        folders.setdefault(m[1], []).append(m)
    md = [
        "# DAX Measure Library",
        "",
        "_Generated from `scripts/measures.py` by `scripts/build_powerbi_assets.py` - edit the Python source, not this file._",
        "",
        f"**{len(MEASURES)} explicit measures** in the `_Measures` table, organised in display folders. "
        "All report visuals use these measures; implicit aggregation of fact columns is avoided "
        "(numeric fact columns are hidden in the model).",
        "",
        "## Conventions",
        "",
        "- **Sales = net sales** (`FactSales[SalesAmount]`, after line discounts). Gross (list-price) sales are reported separately.",
        "- **Profit = net sales - cost of goods** (gross profit). Overheads, shipping and returns are not in the data.",
        "- Ratios are always **ratio of sums** (`DIVIDE(SUM, SUM)`), never an average of row-level percentages.",
        "- `DIVIDE` is used for every division, so a zero or blank denominator returns blank instead of an error.",
        "- Comparison measures (MoM, YoY, YTD growth) return **blank when the comparison period has no data** "
        "(e.g. any 2023 YoY), rather than showing a misleading +100% or -100%.",
        "- MoM measures only evaluate when exactly one month is in context (`HASONEVALUE(DimDate[YearMonth])`).",
        "- Time intelligence relies on `DimDate` being marked as the date table on `DimDate[Date]` "
        "(contiguous daily calendar, full years 2023-2025).",
        "- Target measures return blank below target grain - see *Sales Target* below.",
        "",
        "## Applying the measures in Power BI Desktop",
        "",
        "1. Create the measure table: **Home > Enter data**, name the table `_Measures`, load it (keep the default column; hide it later).",
        "2. Open **TMDL view**, start a new tab, paste the contents of [`tmdl/measures.tmdl`](tmdl/measures.tmdl) and click **Apply**.",
        "3. If TMDL view is unavailable in your Power BI Desktop version, create each measure manually "
        "(**Modeling > New measure**) using the definitions below, and set the format and display folder shown.",
        "",
        "## Contents",
        "",
    ]
    for folder, items in folders.items():
        md.append(f"- **{folder}**: " + ", ".join(i[0] for i in items))
    md.append("")
    for folder, items in folders.items():
        md += [f"## {folder}", "", "| Measure | Format | Definition |", "|---|---|---|"]
        for name, _, fmt, desc, _ in items:
            md.append(f"| {name} | `{fmt or 'Text'}` | {desc} |")
        md.append("")
        for name, _, fmt, desc, expr in items:
            md += [f"### {name}", "", desc, "", "```dax", f"{name} =", expr.strip(), "```", ""]
    return "\n".join(md)


def build_pq(table: str) -> str:
    cols = SCHEMA[table]["columns"]
    nullable = [c[0] for c in cols if c[0] in NULLABLE_TEXT_TO_NULL]
    type_list = ",\n        ".join(f'{{"{c[0]}", {c[1]}}}' for c in cols)
    steps = [
        f"// {table}: {SCHEMA[table]['description']}",
        f"// Grain: {SCHEMA[table]['grain']}",
        "// Generated by scripts/build_powerbi_assets.py. Requires the text parameter DataFolder",
        "// (full path to data/processed/ ending with a backslash).",
        "let",
        f'    Source = Csv.Document(File.Contents(DataFolder & "{table}.csv"), '
        f'[Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),',
        "    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),",
    ]
    prev = "PromotedHeaders"
    if nullable:
        steps.append("    // Blank text in nullable columns -> null before typing (open orders have no ship date)")
        steps.append(f"    BlanksToNull = Table.ReplaceValue({prev}, \"\", null, Replacer.ReplaceValue, "
                     f"{{{', '.join(chr(34) + n + chr(34) for n in nullable)}}}),")
        prev = "BlanksToNull"
    steps += [
        "    // Explicit types with en-US culture so ISO dates and decimal points parse identically on any PC",
        f"    ChangedTypes = Table.TransformColumnTypes({prev}, {{",
        f"        {type_list}",
        '    }, "en-US")',
        "in",
        "    ChangedTypes",
    ]
    return "\n".join(steps) + "\n"


PARAM_PQ = r"""// DataFolder parameter: Home > Transform data > Manage Parameters > New Parameter
// Name: DataFolder | Type: Text | Current value: full path to data\processed\ (keep the trailing backslash)
// Equivalent M (Advanced Editor of a blank query named DataFolder). M strings do not escape backslashes.
"C:\Projects\sales-performance-bi-dashboard\data\processed\" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]
"""


def build_dictionary() -> str:
    md = [
        "# Data Dictionary",
        "",
        "_Generated from `scripts/schema.py` by `scripts/build_powerbi_assets.py`. "
        "All data is **synthetic** and describes the fictional retailer Meridian Home & Office Co._",
        "",
        "Files: `data/processed/<Table>.csv` (UTF-8, comma-delimited, ISO dates `YYYY-MM-DD`, "
        "logical values `true`/`false`, blank = null).",
        "",
        "**Hidden** = hidden from report users in the Power BI model (keys, sort columns, and numeric fact columns "
        "that are exposed only through explicit measures).",
        "",
        "| Table | Grain | Description |",
        "|---|---|---|",
    ]
    for t in LOAD_ORDER:
        md.append(f"| {t} | {SCHEMA[t]['grain']} | {SCHEMA[t]['description']} |")
    md.append("")
    for t in LOAD_ORDER:
        md += [f"## {t}", "", f"{SCHEMA[t]['description']}  ", f"**Grain:** {SCHEMA[t]['grain']}", "",
               "| Column | Type | Hidden | Meaning | Business purpose |", "|---|---|---|---|---|"]
        for name, typ, desc, purpose, hidden in SCHEMA[t]["columns"]:
            nice = {"Int64.Type": "Whole number", "type text": "Text", "type date": "Date",
                    "Currency.Type": "Fixed decimal (currency)", "type number": "Decimal",
                    "Percentage.Type": "Percentage", "type logical": "True/False"}[typ]
            md.append(f"| {name} | {nice} | {'Yes' if hidden else ''} | {desc} | {purpose} |")
        md.append("")
    md += [
        "## Calculation rules",
        "",
        "| Field | Formula | Notes |",
        "|---|---|---|",
        "| GrossSales | Quantity x UnitPrice | Rounded to cents |",
        "| DiscountAmount | GrossSales x DiscountPct | Rounded to cents. Discount is applied **before** revenue is recognised |",
        "| SalesAmount (net sales, 'Sales') | GrossSales - DiscountAmount | Revenue used in every KPI |",
        "| CostAmount | Quantity x UnitCost | Standard cost at time of sale |",
        "| Profit | SalesAmount - CostAmount | Gross profit; no overheads, freight or returns |",
        "| DaysToShip | ShipDate - OrderDate | Blank for open orders |",
        "",
    ]
    return "\n".join(md)


def main() -> None:
    pq_dir = ROOT / "powerbi" / "power_query"
    tmdl_dir = ROOT / "powerbi" / "tmdl"
    pq_dir.mkdir(parents=True, exist_ok=True)
    tmdl_dir.mkdir(parents=True, exist_ok=True)
    (ROOT / "docs").mkdir(exist_ok=True)

    (pq_dir / "DataFolder.pq").write_text(PARAM_PQ, encoding="utf-8")
    for t in LOAD_ORDER:
        (pq_dir / f"{t}.pq").write_text(build_pq(t), encoding="utf-8")
    (tmdl_dir / "measures.tmdl").write_text(build_tmdl(), encoding="utf-8")
    (ROOT / "powerbi" / "dax_measures.md").write_text(build_dax_md(), encoding="utf-8")
    (ROOT / "docs" / "data_dictionary.md").write_text(build_dictionary(), encoding="utf-8")
    print(f"Wrote {len(LOAD_ORDER) + 1} Power Query scripts, {len(MEASURES)} measures (TMDL + docs), data dictionary.")


if __name__ == "__main__":
    main()
