# Testing & Validation

Validation is split into what was **verified automatically** in this repository and what must be **checked manually in Power BI Desktop**. The two are kept separate so the project never claims more than has been tested.

## 1. Automated checks (verified)

Run: `python scripts/validate_data.py` (or `python tests/data_quality_checks.py`, or `pytest tests/data_quality_checks.py`).
Latest results: [validation_report.md](validation_report.md) - **17/17 passed**.

| Area | What is checked |
|---|---|
| Structure | Each processed CSV matches `scripts/schema.py` column-for-column |
| Keys | Primary keys, business keys (OrderID + line, ProductName, CustomerID) and target grain are unique |
| Relationships | Every fact and target key exists in its dimension; order and ship dates fall inside DimDate; target Region/Category values match the dimension values used by TREATAS |
| Nulls | Only documented nulls exist (ship date on open orders; first/last order date for customers without orders) |
| Dates | DimDate is contiguous full years; sort keys are 1:1; ship date >= order date; DaysToShip correct |
| Financials | Gross, discount, net sales, cost and profit reconcile on every line within half a cent |
| Aggregation | Totals by region, category, channel, segment and year equal the grand total; customer lifetime values agree with the fact |
| KPIs | Reference KPI values recompute from the fact; profit margin is a ratio of sums; YoY growth for 2023 is blank |
| Targets | Complete Month x Region x Category x Channel grid, positive, same months as sales, reconciles to the finance workbook |
| Cleaning | Raw rows - duplicates - test rows = fact rows; no test or malformed order IDs remain; text is trimmed and conformed |
| DAX (static) | Every `Table[Column]` and `[Measure]` reference in all 78 measures exists; parentheses balance; no duplicate names |
| Generated docs | Data dictionary and TMDL script cover every column and measure; theme JSON is valid |
| Reproducibility | Regenerating with seed 42 reproduces every raw file byte-for-byte (Excel compared by content) |

The checks were also mutation-tested during development (a deliberately broken profit value, a missing product key and a bad DAX column reference were each caught).

## 2. Independent KPI calculation (verified in Python)

`scripts/calculate_kpis.py` re-implements each measure's logic in pandas and writes [kpi_reference.md](kpi_reference.md). These are the **expected** values for the Power BI report. They are not Power BI results.

## 3. Manual checks in Power BI Desktop (pending - requires Power BI)

Tick each item after building the report.

**Load and model**

- [ ] Row counts match `validation_report.md` for all seven tables.
- [ ] No blank rows appear in any slicer (would indicate a referential-integrity problem).
- [ ] DimDate is marked as date table; Auto date/time is off.
- [ ] Exactly one inactive relationship (ShipDate); no bidirectional relationships.

**Core measures** (matrix, no filters - compare with section 1 of `kpi_reference.md`)

- [ ] Total Sales $9,153,711 / Total Profit $2,584,676 / Profit Margin % 28.2% / Total Orders 16,472 / Total Customers 1,251 / AOV $555.71.
- [ ] Discount Rate % 7.2%; List Margin % 33.4%.

**Time intelligence** (matrix by Year, then by YearMonth)

- [ ] Sales YoY Growth %: blank, 13.1%, -0.3%.
- [ ] Dec 2025: Sales Previous Month $322,499; MoM 10.0%; Rolling 3M Avg $320,118.
- [ ] Jan 2023: Sales Previous Month and MoM are blank.
- [ ] Jun 2025: Sales YTD $1,421,590; Sales PYTD $1,448,911.
- [ ] At Year level, Sales MoM Growth % is blank (single-month guard).

**Targets**

- [ ] Target Achievement % by year: 101.3%, 101.9%, 90.7%; by region and channel as in `kpi_reference.md`.
- [ ] Sales Target is blank when filtering a single State, a Subcategory, or a customer Segment; populated for a Category.
- [ ] Filtering a channel and a region together shows a target (grain supports it).

**Product and customer**

- [ ] Top 10 products table matches the reference list; Top 10 Products Sales Share % = 43.2%.
- [ ] Product Sales Contribution % sums to 100% in a product table.
- [ ] Top 20% Customers Sales Share % = 71.7%; Top Customer by Sales = Redwoodvalley Consulting LLC.
- [ ] New Customers by year = 818 / 261 / 172.

**Profitability**

- [ ] Profit margin by discount band matches (31.0%, 27.9%, 23.6%, 12.6%, -2.4%).
- [ ] Loss-Making Lines = 228.

**Report behaviour**

- [ ] Slicers are synced on all six pages; Reset button clears them.
- [ ] Drill-through to Product Detail and Customer Detail keeps the filter context; Back button works.
- [ ] Dynamic titles and period labels change with slicers.
- [ ] Conditional formatting colours match status measures.
- [ ] Performance Analyzer: no visual slower than ~1 s on the full dataset.

## 4. Known assumptions behind the tests

- Calendar year = fiscal year; data ends 31 Dec 2025.
- Time-intelligence comparisons use calendar dates (`SAMEPERIODLASTYEAR`), so a partial month is compared with the same partial month last year.
- Target comparisons assume month-level date filters (see data model limitations).
