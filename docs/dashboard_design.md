# Dashboard Design Specification

This is the build specification for the six-page Power BI report plus drill-through and tooltip pages. Positions are in pixels on the default **16:9 canvas (1280 x 720)** so the report can be reproduced precisely in Power BI Desktop (Format pane > General > Properties > Size and position).

> Status: specification. The pages are built in Power BI Desktop by following this document and [`powerbi/README.md`](../powerbi/README.md). No screenshots are included until that build is done.

## 1. Design system

### Colour palette (applied by `powerbi/theme/meridian_executive_theme.json`)

| Role | Hex | Use |
|---|---|---|
| Navy (primary) | `#1F3A5F` | Primary series, KPI values, header text |
| Teal (accent / good) | `#0F9D8A` | Second series, on-target, growth, healthy margin |
| Slate | `#64748B` | Third series, secondary text |
| Sky | `#5FA8D3` | Fourth series |
| Light slate | `#94A3B8` | Comparison series (prior year, target), moderate margin |
| Amber | `#E08E0B` | Near target, low margin (warning) |
| Red | `#C0392B` | Below target, loss, decline (use sparingly) |
| Page background | `#F4F6F9` | Canvas |
| Card background | `#FFFFFF` | All visuals |

Rules: one accent colour per visual; prior-year and target series always light slate; red only for genuinely bad states (below 95% of target, negative margin or growth). Status colours come from measures (`Target Status Color`, `Margin Status Color`, `Growth Color`) so they are consistent everywhere.

### Typography

Segoe UI throughout. Page title 20 pt Semibold navy; visual titles 11 pt Semibold; labels 9 pt slate; KPI values 24 pt Semibold navy.

### Number formats

| Type | Format | Example |
|---|---|---|
| Currency in cards | Display units Auto, 1 decimal | $9.2M |
| Currency in tables | `$#,0` | $612,913 |
| Unit prices / AOV | `$#,0.00` | $555.71 |
| Percentages | `0.0%` | 28.2% |
| Counts | `#,0` | 16,472 |
| Months | `MMM yyyy` or YearMonth `2025-12` | Dec 2025 |

### Layout grid (all pages)

| Zone | Position (x, y, w, h) | Contents |
|---|---|---|
| Header | 0, 0, 1280, 64 | Page title (16, 10, 560, 30); subtitle card with `Report Period Label` and `Filter Context Summary` (16, 40, 760, 20); `Data Through Label` (900, 40, 364, 20, right-aligned) |
| Navigation | 780, 8, 484, 28 | Page navigator (Insert > Buttons > Navigator > Page navigator), 6 buttons, selected state navy fill |
| Filter strip | 16, 72, 1248, 40 | Slicers (dropdown style): Year (16, 72, 180, 40), Region (204), Category (392), Channel (580); page-specific slicer at 768; Reset filters button (1148, 72, 116, 40) |
| KPI row | 16, 120, 1248, 88 | 6 cards of 201 x 88 with 8 px gaps at x = 16, 225, 434, 643, 852, 1061 |
| Main area | 16, 220, 1248, 484 | Visuals; 12 px gutters; 16 px bottom margin |

Slicers are **synced across all six pages** (View > Sync slicers) so a selection follows the user.

## 2. Page specifications

Each page lists its business question, visuals, how to read them, the management action they support, and data limitations.

---

### Page 1 - Executive Sales Overview

**Business question:** How is the business performing overall, and where should management focus?

| Visual | Position (x, y, w, h) | Fields / measures | Formatting |
|---|---|---|---|
| KPI: Total Sales | 16, 120, 201, 88 | `Total Sales`; reference label `KPI Sales Subtitle` | Card (new) |
| KPI: Total Profit | 225, 120, 201, 88 | `Total Profit`; reference label `Profit YoY Growth %` | |
| KPI: Profit Margin % | 434, 120, 201, 88 | `Profit Margin %`; reference label `Margin Status` | Value colour = `Margin Status Color` |
| KPI: Total Orders | 643, 120, 201, 88 | `Total Orders`; reference label `Orders YoY Growth %` | |
| KPI: Sales YoY Growth % | 852, 120, 201, 88 | `Sales YoY Growth %` | Value colour = `Growth Color` |
| KPI: Target Achievement % | 1061, 120, 203, 88 | `Target Achievement %`; reference label `Remaining Sales to Target` | Value colour = `Target Status Color` |
| Monthly net sales vs target | 16, 220, 780, 236 | Line and clustered column: X = DimDate[MonthStartDate] (continuous); columns = `Total Sales`; line = `Sales Target` | Title = `Title Monthly Sales Trend` (fx); target line light slate, dashed |
| Monthly profit and margin | 16, 468, 780, 236 | Line chart: X = MonthStartDate; Y = `Total Profit`; secondary Y = `Profit Margin %` | Margin line teal |
| Sales and target achievement by region | 808, 220, 456, 170 | Clustered bar: Y = Region; X = `Total Sales`; data label = `Target Achievement %` | Bar colour (fx) = `Target Status Color` |
| Sales by category | 808, 400, 456, 150 | Clustered bar: Y = Category; X = `Total Sales`; tooltip = Margin tooltip page | Navy bars, sorted descending |
| Key insights | 808, 560, 456, 144 | Text box with 3 bullets (see section 4); or Smart narrative visual | Small caption: "Illustrative findings from synthetic data" |

**Interpretation:** Columns above the dashed line = month beat target. A teal achievement card means at or above target; amber 95-99.9%; red below 95%.
**Management action:** Focus review meetings on red regions/categories; open Regional or Product pages to diagnose.
**Limitations:** Target is blank if the user filters a state, subcategory, product or customer attribute (by design). The subtitle explains this via `Target Availability Note`.

---

### Page 2 - Sales Trend Analysis

**Business question:** How does performance change over time, and is there a seasonal pattern?

| Visual | Position | Fields / measures | Notes |
|---|---|---|---|
| KPI cards (5) | KPI row (5 cards, widths 245) | `Sales YTD`, `Sales PYTD`, `Sales YTD Growth %`, `Sales Rolling 3M Avg`, `Sales MoM Growth %` | MoM card shows a value only when one month is selected - add a YearMonth dropdown slicer at 768, 72 |
| Seasonality: monthly sales by year | 16, 220, 616, 236 | Line chart: X = DimDate[MonthShort]; Y = `Total Sales`; Legend = Year | Each year a line; shows whether peaks repeat |
| Quarterly sales and YoY growth | 648, 220, 616, 236 | Line and clustered column: X = YearQuarter; columns = `Total Sales`; line = `Sales YoY Growth %` | Growth line blank for 2023 (expected) |
| Sales and profit trend | 16, 468, 616, 236 | Line chart: X = MonthStartDate; Y = `Total Sales`, `Total Profit`; + `Sales Rolling 3M Avg` | Shows whether profit tracks sales |
| Period matrix with drill-down | 648, 468, 616, 236 | Matrix: Rows = Calendar hierarchy (Year > Quarter > MonthName); Values = `Total Sales`, `Sales Previous Year`, `Sales YoY Growth %`, `Sales MoM Growth %`, `Profit Margin %` | Drill-down enabled; YoY % background colour = `Growth Color` |

**Interpretation:** Seasonality is claimed only if the same months peak in every year (check the line chart). In this dataset Nov-Dec deliver about 21% of annual sales in each of the three years.
**Action:** Plan stock, staffing and promotions around repeatable peaks; investigate months where growth turns negative.
**Limitations:** Three years of data; no 2022 comparison, so 2023 YoY is blank.

---

### Page 3 - Product Performance

**Business question:** Which products and categories drive sales and profit, and which sell well but earn weak margins?

| Visual | Position | Fields / measures | Notes |
|---|---|---|---|
| KPI cards (6) | KPI row | `Total Sales`, `Total Profit`, `Profit Margin %`, `Top Product by Sales`, `Top 10 Products Sales Share %`, `Products with Negative Profit` | |
| Sales by category > subcategory | 16, 220, 400, 484 | Clustered bar with Product hierarchy on Y (drill-down on); X = `Total Sales`; tooltip = `Profit Margin %`, `Category Sales Contribution %` | Bar colour (fx) = `Margin Status Color` |
| Top 10 products by revenue | 428, 220, 412, 236 | Table: ProductName, `Product Sales Rank`, `Total Sales`, `Product Sales Contribution %`, `Profit Margin %` | Visual filter: ProductName Top N = 10 by `Total Sales`; data bars on sales; margin font colour (fx) = `Margin Status Color` |
| Bottom 10 products by profit | 428, 468, 412, 236 | Table: ProductName, `Product Profit Rank (Lowest First)`, `Total Sales`, `Total Profit`, `Profit Margin %` | Filter: Bottom N = 10 by `Total Profit` |
| Sales vs margin quadrant | 852, 220, 412, 484 | Scatter: Details = ProductName; X = `Total Sales`; Y = `Profit Margin %`; Size = `Total Units Sold`; Legend = Category | Analytics pane: average lines on X and Y. Bottom-right quadrant = high sales, low margin |

**Interpretation:** Products in the bottom-right of the scatter sell well but contribute little profit per dollar - candidates for price review, cost negotiation or bundling with high-margin accessories.
**Action:** Review pricing and supplier costs for low-margin best sellers; promote high-margin categories.
**Limitations:** Margin is gross margin only; logistics and returns costs (often material for large items) are not in the data.

Drill-through: right-click any product > Drill through > **Product Detail**.

---

### Page 4 - Regional Performance

**Business question:** Which regions perform best against target, and where is growth slowing?

| Visual | Position | Fields / measures | Notes |
|---|---|---|---|
| KPI cards (6) | KPI row | `Total Sales`, `Sales YoY Growth %`, `Target Achievement %`, `Sales vs Target`, `Profit Margin %`, `Average Order Value` | |
| Region scorecard | 16, 220, 616, 200 | Table: Region, `Total Sales`, `Sales Target`, `Target Achievement %`, `Sales YoY Growth %`, `Total Profit`, `Profit Margin %` | Achievement % background (fx) = `Target Status Color` |
| Sales vs target by region | 648, 220, 616, 200 | Clustered column: X = Region; Y = `Total Sales`, `Sales Target` | Target series light slate |
| Regional monthly trend | 16, 432, 616, 272 | Line chart with small multiples by Region: X = MonthStartDate; Y = `Total Sales`, `Sales Target` | Shared Y-axis to compare scale |
| State drill matrix | 648, 432, 300, 272 | Matrix: Geography hierarchy (Region > State > City); `Total Sales`, `Sales YoY Growth %`, `Profit Margin %` | Target intentionally not shown below region |
| Filled map (optional) | 960, 432, 304, 272 | Filled map / Azure map: Location = State; colour saturation = `Total Sales`; tooltips = margin, YoY | Include only if maps are enabled in the tenant; the matrix carries the same information |

**Interpretation:** Use the scorecard for "which region missed and by how much"; use small multiples for "since when". The map shows concentration only - it does not normalise for population, so do not read darker states as better-performing markets.
**Action:** Prioritise regions with repeated misses; check whether a miss is a target-setting issue (a spike the year before) or a demand decline.
**Limitations:** Targets exist only at region level.

---

### Page 5 - Customer Insights

**Business question:** Who are our most valuable customers, how concentrated is revenue, and how often do customers come back?

| Visual | Position | Fields / measures | Notes |
|---|---|---|---|
| KPI cards (6) | KPI row | `Total Customers`, `Average Order Value`, `Sales per Customer`, `Repeat Customer Rate %`, `New Customers`, `Top 20% Customers Sales Share %` | |
| Top 15 customers | 16, 220, 520, 484 | Table: CustomerName, Segment, `Customer Sales Rank`, `Total Sales`, `Total Orders`, `Customer Sales Contribution %`, `Profit Margin %` | Top N = 15 filter; data bars on sales. Drill-through to **Customer Detail** |
| Sales by segment | 548, 220, 350, 236 | Clustered bar: Segment; `Total Sales`; tooltip `Total Customers`, `Average Order Value` | |
| Value tier contribution | 910, 220, 354, 236 | Clustered column: ValueTier; `Total Sales` and line `Customer Sales Contribution %` | Shows Pareto: few customers, most sales |
| New vs returning customers by year | 548, 468, 350, 236 | Stacked column: X = Year; `New Customers`, `Returning Customers` | Caption: "2023: all buyers count as new - no earlier history" |
| Purchase frequency | 910, 468, 354, 236 | Clustered bar: PurchaseFrequency; `Total Customers` (distinct) and `Total Sales` | Static tier, documented rule |

**Interpretation:** High concentration means account management matters more than mass marketing - and that losing one key account is a material risk.
**Action:** Assign account owners to A-tier customers; design a second-order incentive for one-time buyers.
**Limitations:** No margin-after-service-cost or lifetime value; "repeat" means 2+ orders within the selected period, not loyalty.

---

### Page 6 - Profitability & Discount Analysis

**Business question:** What drives profit, and where are margins being lost?

| Visual | Position | Fields / measures | Notes |
|---|---|---|---|
| KPI cards (6) | KPI row | `Total Profit`, `Profit Margin %`, `Discount Rate %`, `Margin Erosion from Discounts`, `Discounted Sales Share %`, `Loss-Making Sales` | |
| Margin by discount band | 16, 220, 616, 236 | Line and clustered column: X = DiscountBand; columns = `Total Sales`; line = `Profit Margin %` | Sorted by DiscountBandOrder |
| Discount rate vs margin by product | 648, 220, 616, 236 | Scatter: Details = ProductName; X = `Discount Rate %`; Y = `Profit Margin %`; Size = `Total Sales`; Legend = Category | Caption: "Association, not causation" |
| Margin heatmap: category x region | 16, 468, 400, 236 | Matrix: Rows = Category; Columns = Region; Values = `Profit Margin %` | Background colour scale (fx) - diverging from amber to teal |
| Subcategory margin ranking | 428, 468, 412, 236 | Clustered bar: Subcategory; `Profit Margin %`; tooltip `Total Sales`, `Discount Rate %`, `List Margin %` | Colour (fx) = `Margin Status Color`; sorted ascending |
| Profit drivers summary | 852, 468, 412, 236 | Table: Category, `List Margin %`, `Discount Rate %`, `Profit Margin %`, `Margin Erosion from Discounts`, `Loss-Making Lines` | Explains *why* margin differs: list margin vs discounting |

**Interpretation:** Separate two drivers: low **list margin** (product economics - e.g. laptops) and **discount erosion** (pricing decisions - e.g. furniture promotions). The discount-band chart shows the arithmetic effect of deeper discounts on margin; it does not prove discounts reduced total profit, because we cannot see the sales that would have happened without them.
**Action:** Set discount guardrails (e.g. approval above 20%), test smaller promotions on tables and desks, and review list pricing on low-margin best sellers.
**Limitations:** No price-elasticity data, no promotion calendar, no returns.

## 3. Supporting pages

| Page | Type | Size | Contents |
|---|---|---|---|
| Product Detail | Drill-through (field: DimProduct[ProductName]; keep all filters on) | 1280 x 720 | Product name title (`SELECTEDVALUE`-based card), KPI cards (sales, profit, margin, units, discount rate), monthly sales line, sales by channel bar, sales by discount band, top customers for the product. Back button top-left |
| Customer Detail | Drill-through (field: DimCustomer[CustomerName]) | 1280 x 720 | Segment, ValueTier, CustomerSince, FirstOrderDate cards; sales/orders/AOV; monthly sales; category mix; recent orders table (OrderID, OrderDate, ChannelName, `Total Sales`) |
| Margin Tooltip | Tooltip page (Page information > Allow use as tooltip) | 320 x 240 | `Total Sales`, `Total Profit`, `Profit Margin %`, `Discount Rate %`, `Target Achievement %`, `Sales YoY Growth %`. Assign to category/region/subcategory visuals (Format > Tooltips > Report page) |

## 4. Interactivity

| Feature | Implementation | Business purpose |
|---|---|---|
| Date slicer | Year dropdown on all pages; YearMonth dropdown on Trend page; optional between-dates slicer on DimDate[Date] | Answer "how did we do this year / this month" |
| Region, Category, Channel slicers | Dropdown, multi-select, synced across pages | Managers focus on their area |
| Cross-filtering | Default *Filter* interactions; set KPI cards to *None* from the trend visuals where a single month would make cards confusing (Format > Edit interactions) | Click a region bar to see its products and customers |
| Drill-down | Calendar hierarchy (Year > Quarter > Month > Date) and Product hierarchy (Category > Subcategory > Product) | From summary to detail without leaving the page |
| Drill-through | Product Detail, Customer Detail | One-click deep dive |
| Navigation | Page navigator button group in the header; Back buttons on drill-through pages | App-like experience |
| Tooltips | Margin Tooltip report page on bar charts | Context without clutter |
| Dynamic titles | `Title Monthly Sales Trend`, `Report Period Label`, `Filter Context Summary` via Format > Title > fx | User always knows what is filtered |
| Reset filters | Bookmark "Default view" (slicers cleared, Data option on) linked to the Reset button; in the Power BI service the built-in *Reset to default* also works | Recover from heavy filtering |
| Consistent behaviour | Same slicer positions, colours, formats and interaction settings on every page | Low learning curve |

## 5. Key-insights panel text (Executive page)

Replace with current figures if the data is regenerated. From the synthetic dataset (seed 42), full period:

- Sales flat in 2025 (-0.3% YoY) after +13.1% in 2024; 2025 closed at 90.7% of target.
- B2B Wholesale (51% of sales) fell 6.0% in 2025 while Online grew 6.3% and Marketplace 18.9%.
- Laptops are 25% of sales at a 10.5% margin - the largest single drag on overall margin.

## 6. Accessibility

- All status colours are paired with text (`Target Status`, `Margin Status`) or values, never colour alone.
- Minimum font 9 pt; contrast of slate `#475569` on white meets WCAG AA for text.
- Alt text set on every visual (Format > General > Alt text) describing the business question it answers.
- Tab order set in the Selection pane: header > slicers > KPIs > main visuals.
