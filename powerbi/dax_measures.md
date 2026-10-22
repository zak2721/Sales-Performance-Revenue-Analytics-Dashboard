# DAX Measure Library

_Generated from `scripts/measures.py` by `scripts/build_powerbi_assets.py` - edit the Python source, not this file._

**78 explicit measures** in the `_Measures` table, organised in display folders. All report visuals use these measures; implicit aggregation of fact columns is avoided (numeric fact columns are hidden in the model).

## Conventions

- **Sales = net sales** (`FactSales[SalesAmount]`, after line discounts). Gross (list-price) sales are reported separately.
- **Profit = net sales - cost of goods** (gross profit). Overheads, shipping and returns are not in the data.
- Ratios are always **ratio of sums** (`DIVIDE(SUM, SUM)`), never an average of row-level percentages.
- `DIVIDE` is used for every division, so a zero or blank denominator returns blank instead of an error.
- Comparison measures (MoM, YoY, YTD growth) return **blank when the comparison period has no data** (e.g. any 2023 YoY), rather than showing a misleading +100% or -100%.
- MoM measures only evaluate when exactly one month is in context (`HASONEVALUE(DimDate[YearMonth])`).
- Time intelligence relies on `DimDate` being marked as the date table on `DimDate[Date]` (contiguous daily calendar, full years 2023-2025).
- Target measures return blank below target grain - see *Sales Target* below.

## Applying the measures in Power BI Desktop

1. Create the measure table: **Home > Enter data**, name the table `_Measures`, load it (keep the default column; hide it later).
2. Open **TMDL view**, start a new tab, paste the contents of [`tmdl/measures.tmdl`](tmdl/measures.tmdl) and click **Apply**.
3. If TMDL view is unavailable in your Power BI Desktop version, create each measure manually (**Modeling > New measure**) using the definitions below, and set the format and display folder shown.

## Contents

- **01 Sales**: Total Sales, Gross Sales, Total Orders, Total Order Lines, Total Units Sold, Total Customers, Average Order Value, Average Selling Price, Sales per Customer
- **02 Profitability**: Total Cost, Total Profit, Profit Margin %, Average Profit per Order, Discount Amount, Discount Rate %, List Margin %, Margin Erosion from Discounts, Discounted Sales Share %, Profit Margin % (Full-Price Lines), Profit Margin % (Discounted Lines), Loss-Making Lines, Loss-Making Sales, Loss on Loss-Making Lines, Products with Negative Profit, Margin Status, Margin Status Color
- **03 Time Intelligence**: Sales Previous Month, Sales MoM Change, Sales MoM Growth %, Sales Previous Year, Sales YoY Change, Sales YoY Growth %, Sales YTD, Sales PYTD, Sales YTD Growth %, Profit YTD, Profit Previous Year, Profit YoY Growth %, Orders YoY Growth %, AOV YoY Growth %, Sales Rolling 3M Avg
- **04 Targets**: Sales Target, Sales vs Target, Target Achievement %, Remaining Sales to Target, Sales Target YTD, Target Achievement % YTD, Target Status, Target Status Color
- **05 Product & Customer**: Product Sales Contribution %, Category Sales Contribution %, Customer Sales Contribution %, Product Sales Rank, Product Profit Rank (Lowest First), Customer Sales Rank, Top Product by Sales, Top Customer by Sales, Top 10 Products Sales Share %, Top 10 Customers Sales Share %, Top 20% Customers Sales Share %, Repeat Customers, Repeat Customer Rate %, Orders per Customer, New Customers, Returning Customers
- **06 Operations**: Open Orders, Average Days to Ship, Sales by Ship Date
- **07 Labels & UX**: Report Period Label, Data Through Label, Selected Region Label, Selected Channel Label, Selected Category Label, Filter Context Summary, Title Monthly Sales Trend, KPI Sales Subtitle, Target Availability Note, Growth Color

## 01 Sales

| Measure | Format | Definition |
|---|---|---|
| Total Sales | `\$#,0;(\$#,0);\$#,0` | Net sales (revenue after line discounts). The 'Sales' figure used everywhere in the report. |
| Gross Sales | `\$#,0;(\$#,0);\$#,0` | Sales at list price before discounts (Quantity x UnitPrice). |
| Total Orders | `#,0` | Number of distinct orders. |
| Total Order Lines | `#,0` | Number of order lines (fact rows). |
| Total Units Sold | `#,0` | Units sold. |
| Total Customers | `#,0` | Distinct customers who placed at least one order in the current filter context. |
| Average Order Value | `\$#,0.00;(\$#,0.00);\$#,0.00` | Net sales per order. |
| Average Selling Price | `\$#,0.00;(\$#,0.00);\$#,0.00` | Net sales per unit (after discount). |
| Sales per Customer | `\$#,0;(\$#,0);\$#,0` | Net sales per active customer. |

### Total Sales

Net sales (revenue after line discounts). The 'Sales' figure used everywhere in the report.

```dax
Total Sales =
SUM ( FactSales[SalesAmount] )
```

### Gross Sales

Sales at list price before discounts (Quantity x UnitPrice).

```dax
Gross Sales =
SUM ( FactSales[GrossSales] )
```

### Total Orders

Number of distinct orders.

```dax
Total Orders =
DISTINCTCOUNT ( FactSales[OrderID] )
```

### Total Order Lines

Number of order lines (fact rows).

```dax
Total Order Lines =
COUNTROWS ( FactSales )
```

### Total Units Sold

Units sold.

```dax
Total Units Sold =
SUM ( FactSales[Quantity] )
```

### Total Customers

Distinct customers who placed at least one order in the current filter context.

```dax
Total Customers =
DISTINCTCOUNT ( FactSales[CustomerKey] )
```

### Average Order Value

Net sales per order.

```dax
Average Order Value =
DIVIDE ( [Total Sales], [Total Orders] )
```

### Average Selling Price

Net sales per unit (after discount).

```dax
Average Selling Price =
DIVIDE ( [Total Sales], [Total Units Sold] )
```

### Sales per Customer

Net sales per active customer.

```dax
Sales per Customer =
DIVIDE ( [Total Sales], [Total Customers] )
```

## 02 Profitability

| Measure | Format | Definition |
|---|---|---|
| Total Cost | `\$#,0;(\$#,0);\$#,0` | Cost of goods sold (Quantity x UnitCost). |
| Total Profit | `\$#,0;(\$#,0);\$#,0` | Gross profit after discounts = Net sales - Cost. Excludes overheads, shipping and returns (not in the data). |
| Profit Margin % | `0.0%;-0.0%;0.0%` | Total Profit / Total Sales (ratio of sums, never an average of line margins). |
| Average Profit per Order | `\$#,0.00;(\$#,0.00);\$#,0.00` | Gross profit per order. |
| Discount Amount | `\$#,0;(\$#,0);\$#,0` | Value of discounts given (Gross Sales - Net Sales). |
| Discount Rate % | `0.0%;-0.0%;0.0%` | Discount Amount / Gross Sales. Effective discount rate on list-price sales. |
| List Margin % | `0.0%;-0.0%;0.0%` | Margin the same sales would have earned at list price: (Gross Sales - Cost) / Gross Sales. |
| Margin Erosion from Discounts | `0.0%;-0.0%;0.0%` | List Margin % minus Profit Margin %, in percentage points. Arithmetic effect of discounts on margin, holding volume constant - not an estimate of what would have sold without the discount. |
| Discounted Sales Share % | `0.0%;-0.0%;0.0%` | Share of net sales that came from discounted lines. |
| Profit Margin % (Full-Price Lines) | `0.0%;-0.0%;0.0%` | Profit margin on lines sold without a discount. |
| Profit Margin % (Discounted Lines) | `0.0%;-0.0%;0.0%` | Profit margin on lines sold with any discount. |
| Loss-Making Lines | `#,0` | Order lines with negative profit. |
| Loss-Making Sales | `\$#,0;(\$#,0);\$#,0` | Net sales on order lines with negative profit. |
| Loss on Loss-Making Lines | `\$#,0;(\$#,0);\$#,0` | Total (negative) profit on loss-making order lines. |
| Products with Negative Profit | `#,0` | Number of products whose total profit is negative in the current context. |
| Margin Status | `Text` | Margin band used for conditional formatting and tooltips. Thresholds: <0% Loss, <15% Low, <30% Moderate, otherwise Healthy. |
| Margin Status Color | `Text` | Hex colour for conditional formatting (Format > Conditional formatting > Field value). |

### Total Cost

Cost of goods sold (Quantity x UnitCost).

```dax
Total Cost =
SUM ( FactSales[CostAmount] )
```

### Total Profit

Gross profit after discounts = Net sales - Cost. Excludes overheads, shipping and returns (not in the data).

```dax
Total Profit =
SUM ( FactSales[Profit] )
```

### Profit Margin %

Total Profit / Total Sales (ratio of sums, never an average of line margins).

```dax
Profit Margin % =
DIVIDE ( [Total Profit], [Total Sales] )
```

### Average Profit per Order

Gross profit per order.

```dax
Average Profit per Order =
DIVIDE ( [Total Profit], [Total Orders] )
```

### Discount Amount

Value of discounts given (Gross Sales - Net Sales).

```dax
Discount Amount =
SUM ( FactSales[DiscountAmount] )
```

### Discount Rate %

Discount Amount / Gross Sales. Effective discount rate on list-price sales.

```dax
Discount Rate % =
DIVIDE ( [Discount Amount], [Gross Sales] )
```

### List Margin %

Margin the same sales would have earned at list price: (Gross Sales - Cost) / Gross Sales.

```dax
List Margin % =
DIVIDE ( [Gross Sales] - [Total Cost], [Gross Sales] )
```

### Margin Erosion from Discounts

List Margin % minus Profit Margin %, in percentage points. Arithmetic effect of discounts on margin, holding volume constant - not an estimate of what would have sold without the discount.

```dax
Margin Erosion from Discounts =
IF ( NOT ISBLANK ( [Total Sales] ), [List Margin %] - [Profit Margin %] )
```

### Discounted Sales Share %

Share of net sales that came from discounted lines.

```dax
Discounted Sales Share % =
DIVIDE ( CALCULATE ( [Total Sales], FactSales[DiscountPct] > 0 ), [Total Sales] )
```

### Profit Margin % (Full-Price Lines)

Profit margin on lines sold without a discount.

```dax
Profit Margin % (Full-Price Lines) =
CALCULATE ( [Profit Margin %], FactSales[DiscountPct] = 0 )
```

### Profit Margin % (Discounted Lines)

Profit margin on lines sold with any discount.

```dax
Profit Margin % (Discounted Lines) =
CALCULATE ( [Profit Margin %], FactSales[DiscountPct] > 0 )
```

### Loss-Making Lines

Order lines with negative profit.

```dax
Loss-Making Lines =
CALCULATE ( COUNTROWS ( FactSales ), FactSales[Profit] < 0 )
```

### Loss-Making Sales

Net sales on order lines with negative profit.

```dax
Loss-Making Sales =
CALCULATE ( [Total Sales], FactSales[Profit] < 0 )
```

### Loss on Loss-Making Lines

Total (negative) profit on loss-making order lines.

```dax
Loss on Loss-Making Lines =
CALCULATE ( [Total Profit], FactSales[Profit] < 0 )
```

### Products with Negative Profit

Number of products whose total profit is negative in the current context.

```dax
Products with Negative Profit =
COUNTROWS ( FILTER ( VALUES ( DimProduct[ProductKey] ), [Total Profit] < 0 ) )
```

### Margin Status

Margin band used for conditional formatting and tooltips. Thresholds: <0% Loss, <15% Low, <30% Moderate, otherwise Healthy.

```dax
Margin Status =
VAR m = [Profit Margin %]
RETURN
    SWITCH (
        TRUE (),
        ISBLANK ( m ), BLANK (),
        m < 0, "Loss",
        m < 0.15, "Low (<15%)",
        m < 0.30, "Moderate (15-30%)",
        "Healthy (30%+)"
    )
```

### Margin Status Color

Hex colour for conditional formatting (Format > Conditional formatting > Field value).

```dax
Margin Status Color =
VAR m = [Profit Margin %]
RETURN
    SWITCH (
        TRUE (),
        ISBLANK ( m ), BLANK (),
        m < 0, "#C0392B",
        m < 0.15, "#E08E0B",
        m < 0.30, "#94A3B8",
        "#0F9D8A"
    )
```

## 03 Time Intelligence

| Measure | Format | Definition |
|---|---|---|
| Sales Previous Month | `\$#,0;(\$#,0);\$#,0` | Net sales in the previous month. Returns blank unless exactly one month is in context. |
| Sales MoM Change | `\$#,0;(\$#,0);\$#,0` | Net sales minus previous month. Blank when either month has no data (e.g. Jan 2023). |
| Sales MoM Growth % | `0.0%;-0.0%;0.0%` | Month-over-month growth in net sales. |
| Sales Previous Year | `\$#,0;(\$#,0);\$#,0` | Net sales in the same period one year earlier. |
| Sales YoY Change | `\$#,0;(\$#,0);\$#,0` | Net sales minus the same period last year. Blank when there is no prior-year data (all of 2023). |
| Sales YoY Growth % | `0.0%;-0.0%;0.0%` | Year-over-year growth in net sales. |
| Sales YTD | `\$#,0;(\$#,0);\$#,0` | Year-to-date net sales (calendar year) up to the last date in context. |
| Sales PYTD | `\$#,0;(\$#,0);\$#,0` | Prior-year-to-date net sales (same calendar dates one year earlier). |
| Sales YTD Growth % | `0.0%;-0.0%;0.0%` | YTD net sales vs prior YTD. |
| Profit YTD | `\$#,0;(\$#,0);\$#,0` | Year-to-date gross profit. |
| Profit Previous Year | `\$#,0;(\$#,0);\$#,0` | Gross profit in the same period one year earlier. |
| Profit YoY Growth % | `0.0%;-0.0%;0.0%` | Year-over-year growth in gross profit. |
| Orders YoY Growth % | `0.0%;-0.0%;0.0%` | Year-over-year growth in order count. |
| AOV YoY Growth % | `0.0%;-0.0%;0.0%` | Year-over-year change in average order value. |
| Sales Rolling 3M Avg | `\$#,0;(\$#,0);\$#,0` | Average monthly net sales over the 3 months ending at the last date in context. Blank until 3 full months exist. |

### Sales Previous Month

Net sales in the previous month. Returns blank unless exactly one month is in context.

```dax
Sales Previous Month =
IF (
    HASONEVALUE ( DimDate[YearMonth] ),
    CALCULATE ( [Total Sales], DATEADD ( DimDate[Date], -1, MONTH ) )
)
```

### Sales MoM Change

Net sales minus previous month. Blank when either month has no data (e.g. Jan 2023).

```dax
Sales MoM Change =
VAR CurrentSales = [Total Sales]
VAR PreviousSales = [Sales Previous Month]
RETURN
    IF ( NOT ISBLANK ( CurrentSales ) && NOT ISBLANK ( PreviousSales ), CurrentSales - PreviousSales )
```

### Sales MoM Growth %

Month-over-month growth in net sales.

```dax
Sales MoM Growth % =
DIVIDE ( [Sales MoM Change], [Sales Previous Month] )
```

### Sales Previous Year

Net sales in the same period one year earlier.

```dax
Sales Previous Year =
CALCULATE ( [Total Sales], SAMEPERIODLASTYEAR ( DimDate[Date] ) )
```

### Sales YoY Change

Net sales minus the same period last year. Blank when there is no prior-year data (all of 2023).

```dax
Sales YoY Change =
VAR CurrentSales = [Total Sales]
VAR PriorSales = [Sales Previous Year]
RETURN
    IF ( NOT ISBLANK ( CurrentSales ) && NOT ISBLANK ( PriorSales ), CurrentSales - PriorSales )
```

### Sales YoY Growth %

Year-over-year growth in net sales.

```dax
Sales YoY Growth % =
DIVIDE ( [Sales YoY Change], [Sales Previous Year] )
```

### Sales YTD

Year-to-date net sales (calendar year) up to the last date in context.

```dax
Sales YTD =
CALCULATE ( [Total Sales], DATESYTD ( DimDate[Date] ) )
```

### Sales PYTD

Prior-year-to-date net sales (same calendar dates one year earlier).

```dax
Sales PYTD =
CALCULATE ( [Sales YTD], SAMEPERIODLASTYEAR ( DimDate[Date] ) )
```

### Sales YTD Growth %

YTD net sales vs prior YTD.

```dax
Sales YTD Growth % =
VAR ytd = [Sales YTD]
VAR pytd = [Sales PYTD]
RETURN
    IF ( NOT ISBLANK ( ytd ) && NOT ISBLANK ( pytd ), DIVIDE ( ytd - pytd, pytd ) )
```

### Profit YTD

Year-to-date gross profit.

```dax
Profit YTD =
CALCULATE ( [Total Profit], DATESYTD ( DimDate[Date] ) )
```

### Profit Previous Year

Gross profit in the same period one year earlier.

```dax
Profit Previous Year =
CALCULATE ( [Total Profit], SAMEPERIODLASTYEAR ( DimDate[Date] ) )
```

### Profit YoY Growth %

Year-over-year growth in gross profit.

```dax
Profit YoY Growth % =
VAR CurrentProfit = [Total Profit]
VAR PriorProfit = [Profit Previous Year]
RETURN
    IF ( NOT ISBLANK ( CurrentProfit ) && NOT ISBLANK ( PriorProfit ), DIVIDE ( CurrentProfit - PriorProfit, ABS ( PriorProfit ) ) )
```

### Orders YoY Growth %

Year-over-year growth in order count.

```dax
Orders YoY Growth % =
VAR CurrentOrders = [Total Orders]
VAR PriorOrders = CALCULATE ( [Total Orders], SAMEPERIODLASTYEAR ( DimDate[Date] ) )
RETURN
    IF ( NOT ISBLANK ( CurrentOrders ) && NOT ISBLANK ( PriorOrders ), DIVIDE ( CurrentOrders - PriorOrders, PriorOrders ) )
```

### AOV YoY Growth %

Year-over-year change in average order value.

```dax
AOV YoY Growth % =
VAR CurrentAOV = [Average Order Value]
VAR PriorAOV = CALCULATE ( [Average Order Value], SAMEPERIODLASTYEAR ( DimDate[Date] ) )
RETURN
    IF ( NOT ISBLANK ( CurrentAOV ) && NOT ISBLANK ( PriorAOV ), DIVIDE ( CurrentAOV - PriorAOV, PriorAOV ) )
```

### Sales Rolling 3M Avg

Average monthly net sales over the 3 months ending at the last date in context. Blank until 3 full months exist.

```dax
Sales Rolling 3M Avg =
VAR LastDate = MAX ( DimDate[Date] )
VAR Period = DATESINPERIOD ( DimDate[Date], LastDate, -3, MONTH )
VAR MonthsInPeriod = CALCULATE ( DISTINCTCOUNT ( DimDate[YearMonth] ), Period )
RETURN
    IF ( MonthsInPeriod = 3, DIVIDE ( CALCULATE ( [Total Sales], Period ), 3 ) )
```

## 04 Targets

| Measure | Format | Definition |
|---|---|---|
| Sales Target | `\$#,0;(\$#,0);\$#,0` | Net-sales target from the finance plan. Targets exist at Month x Region x Category x Channel. Region and Category are applied with TREATAS; month and channel through physical relationships. Returns blank when the report is filtered below target grain (state/city, subcategory/product/brand/price band, or any customer attribute) because no target exists at that level. |
| Sales vs Target | `\$#,0;(\$#,0);\$#,0` | Net sales minus target (positive = ahead of target). |
| Target Achievement % | `0.0%;-0.0%;0.0%` | Net sales / target. |
| Remaining Sales to Target | `\$#,0;(\$#,0);\$#,0` | Sales still needed to reach target; zero once the target is met. |
| Sales Target YTD | `\$#,0;(\$#,0);\$#,0` | Year-to-date target. |
| Target Achievement % YTD | `0.0%;-0.0%;0.0%` | YTD net sales / YTD target. |
| Target Status | `Text` | On target (>=100%), Near target (95-99.9%), Below target (<95%). |
| Target Status Color | `Text` | Hex colour for conditional formatting of target achievement. |

### Sales Target

Net-sales target from the finance plan. Targets exist at Month x Region x Category x Channel. Region and Category are applied with TREATAS; month and channel through physical relationships. Returns blank when the report is filtered below target grain (state/city, subcategory/product/brand/price band, or any customer attribute) because no target exists at that level.

```dax
Sales Target =
VAR VisibleProducts = COUNTROWS ( VALUES ( DimProduct[ProductKey] ) )
VAR ProductsInVisibleCategories =
    CALCULATE ( COUNTROWS ( DimProduct ), REMOVEFILTERS ( DimProduct ), VALUES ( DimProduct[Category] ) )
VAR VisibleCities = COUNTROWS ( VALUES ( DimGeography[GeographyKey] ) )
VAR CitiesInVisibleRegions =
    CALCULATE ( COUNTROWS ( DimGeography ), REMOVEFILTERS ( DimGeography ), VALUES ( DimGeography[Region] ) )
VAR IsTargetGrain =
    VisibleProducts = ProductsInVisibleCategories
        && VisibleCities = CitiesInVisibleRegions
        && NOT ISCROSSFILTERED ( DimCustomer )
RETURN
    IF (
        IsTargetGrain,
        CALCULATE (
            SUM ( FactSalesTarget[TargetAmount] ),
            TREATAS ( VALUES ( DimProduct[Category] ), FactSalesTarget[Category] ),
            TREATAS ( VALUES ( DimGeography[Region] ), FactSalesTarget[Region] )
        )
    )
```

### Sales vs Target

Net sales minus target (positive = ahead of target).

```dax
Sales vs Target =
VAR TargetValue = [Sales Target]
RETURN
    IF ( NOT ISBLANK ( TargetValue ), [Total Sales] - TargetValue )
```

### Target Achievement %

Net sales / target.

```dax
Target Achievement % =
DIVIDE ( [Total Sales], [Sales Target] )
```

### Remaining Sales to Target

Sales still needed to reach target; zero once the target is met.

```dax
Remaining Sales to Target =
VAR TargetValue = [Sales Target]
RETURN
    IF ( NOT ISBLANK ( TargetValue ), MAX ( 0, TargetValue - [Total Sales] ) )
```

### Sales Target YTD

Year-to-date target.

```dax
Sales Target YTD =
CALCULATE ( [Sales Target], DATESYTD ( DimDate[Date] ) )
```

### Target Achievement % YTD

YTD net sales / YTD target.

```dax
Target Achievement % YTD =
DIVIDE ( [Sales YTD], [Sales Target YTD] )
```

### Target Status

On target (>=100%), Near target (95-99.9%), Below target (<95%).

```dax
Target Status =
VAR a = [Target Achievement %]
RETURN
    SWITCH ( TRUE (), ISBLANK ( a ), BLANK (), a >= 1, "On target", a >= 0.95, "Near target", "Below target" )
```

### Target Status Color

Hex colour for conditional formatting of target achievement.

```dax
Target Status Color =
VAR a = [Target Achievement %]
RETURN
    SWITCH ( TRUE (), ISBLANK ( a ), BLANK (), a >= 1, "#0F9D8A", a >= 0.95, "#E08E0B", "#C0392B" )
```

## 05 Product & Customer

| Measure | Format | Definition |
|---|---|---|
| Product Sales Contribution % | `0.0%;-0.0%;0.0%` | Share of net sales within the products selected by slicers (ALLSELECTED). In a product table, rows sum to 100%. |
| Category Sales Contribution % | `0.0%;-0.0%;0.0%` | Share of the current row's category in selected net sales. At subcategory/product level it returns the parent category's share. |
| Customer Sales Contribution % | `0.0%;-0.0%;0.0%` | Share of net sales within the customers selected by slicers. |
| Product Sales Rank | `#,0` | Rank of a product by net sales among selected products (1 = highest). Use with a Top N visual filter. |
| Product Profit Rank (Lowest First) | `#,0` | Rank of products by profit, lowest first, ignoring products with no sales. Use to list bottom performers. |
| Customer Sales Rank | `#,0` | Rank of a customer by net sales among selected customers. |
| Top Product by Sales | `Text` | Name of the highest-selling product in the current context (for cards and titles). |
| Top Customer by Sales | `Text` | Name of the highest-spending customer in the current context. |
| Top 10 Products Sales Share % | `0.0%;-0.0%;0.0%` | Share of net sales generated by the 10 highest-selling products in the current context (concentration). |
| Top 10 Customers Sales Share % | `0.0%;-0.0%;0.0%` | Share of net sales from the 10 highest-spending customers in the current context. |
| Top 20% Customers Sales Share % | `0.0%;-0.0%;0.0%` | Share of net sales from the top 20% of purchasing customers (Pareto check). |
| Repeat Customers | `#,0` | Customers with 2 or more orders within the current filter context (period, channel, etc.). |
| Repeat Customer Rate % | `0.0%;-0.0%;0.0%` | Repeat Customers / Total Customers in the current context. |
| Orders per Customer | `#,0.0` | Average orders per active customer. |
| New Customers | `#,0` | Active customers whose first order in the dataset (DimCustomer[FirstOrderDate]) falls inside the selected dates. Data starts in Jan 2023, so 2023 counts include customers who may have bought before 2023. |
| Returning Customers | `#,0` | Active customers in the period who had ordered before the period started. |

### Product Sales Contribution %

Share of net sales within the products selected by slicers (ALLSELECTED). In a product table, rows sum to 100%.

```dax
Product Sales Contribution % =
DIVIDE ( [Total Sales], CALCULATE ( [Total Sales], ALLSELECTED ( DimProduct ) ) )
```

### Category Sales Contribution %

Share of the current row's category in selected net sales. At subcategory/product level it returns the parent category's share.

```dax
Category Sales Contribution % =
VAR CategorySales =
    CALCULATE ( [Total Sales], ALLSELECTED ( DimProduct ), VALUES ( DimProduct[Category] ) )
VAR SelectedSales = CALCULATE ( [Total Sales], ALLSELECTED ( DimProduct ) )
RETURN
    DIVIDE ( CategorySales, SelectedSales )
```

### Customer Sales Contribution %

Share of net sales within the customers selected by slicers.

```dax
Customer Sales Contribution % =
DIVIDE ( [Total Sales], CALCULATE ( [Total Sales], ALLSELECTED ( DimCustomer ) ) )
```

### Product Sales Rank

Rank of a product by net sales among selected products (1 = highest). Use with a Top N visual filter.

```dax
Product Sales Rank =
IF (
    ISINSCOPE ( DimProduct[ProductName] ) && NOT ISBLANK ( [Total Sales] ),
    RANKX ( ALLSELECTED ( DimProduct[ProductName] ), [Total Sales], , DESC, DENSE )
)
```

### Product Profit Rank (Lowest First)

Rank of products by profit, lowest first, ignoring products with no sales. Use to list bottom performers.

```dax
Product Profit Rank (Lowest First) =
IF (
    ISINSCOPE ( DimProduct[ProductName] ) && NOT ISBLANK ( [Total Sales] ),
    RANKX (
        FILTER ( ALLSELECTED ( DimProduct[ProductName] ), NOT ISBLANK ( [Total Sales] ) ),
        [Total Profit], , ASC, DENSE
    )
)
```

### Customer Sales Rank

Rank of a customer by net sales among selected customers.

```dax
Customer Sales Rank =
IF (
    ISINSCOPE ( DimCustomer[CustomerName] ) && NOT ISBLANK ( [Total Sales] ),
    RANKX ( ALLSELECTED ( DimCustomer[CustomerName] ), [Total Sales], , DESC, DENSE )
)
```

### Top Product by Sales

Name of the highest-selling product in the current context (for cards and titles).

```dax
Top Product by Sales =
VAR TopProduct = TOPN ( 1, VALUES ( DimProduct[ProductName] ), [Total Sales], DESC )
RETURN
    IF ( NOT ISBLANK ( [Total Sales] ), CONCATENATEX ( TopProduct, DimProduct[ProductName], ", " ) )
```

### Top Customer by Sales

Name of the highest-spending customer in the current context.

```dax
Top Customer by Sales =
VAR TopCustomer = TOPN ( 1, VALUES ( DimCustomer[CustomerName] ), [Total Sales], DESC )
RETURN
    IF ( NOT ISBLANK ( [Total Sales] ), CONCATENATEX ( TopCustomer, DimCustomer[CustomerName], ", " ) )
```

### Top 10 Products Sales Share %

Share of net sales generated by the 10 highest-selling products in the current context (concentration).

```dax
Top 10 Products Sales Share % =
VAR Top10 = TOPN ( 10, VALUES ( DimProduct[ProductName] ), [Total Sales], DESC )
RETURN
    DIVIDE ( CALCULATE ( [Total Sales], Top10 ), [Total Sales] )
```

### Top 10 Customers Sales Share %

Share of net sales from the 10 highest-spending customers in the current context.

```dax
Top 10 Customers Sales Share % =
VAR Top10 = TOPN ( 10, VALUES ( DimCustomer[CustomerKey] ), [Total Sales], DESC )
RETURN
    DIVIDE ( CALCULATE ( [Total Sales], Top10 ), [Total Sales] )
```

### Top 20% Customers Sales Share %

Share of net sales from the top 20% of purchasing customers (Pareto check).

```dax
Top 20% Customers Sales Share % =
VAR Buyers = FILTER ( VALUES ( DimCustomer[CustomerKey] ), NOT ISBLANK ( [Total Sales] ) )
VAR TopCount = ROUNDUP ( COUNTROWS ( Buyers ) * 0.2, 0 )
VAR TopCustomers = TOPN ( TopCount, Buyers, [Total Sales], DESC )
RETURN
    DIVIDE ( CALCULATE ( [Total Sales], TopCustomers ), [Total Sales] )
```

### Repeat Customers

Customers with 2 or more orders within the current filter context (period, channel, etc.).

```dax
Repeat Customers =
COUNTROWS (
    FILTER ( VALUES ( FactSales[CustomerKey] ), CALCULATE ( DISTINCTCOUNT ( FactSales[OrderID] ) ) >= 2 )
)
```

### Repeat Customer Rate %

Repeat Customers / Total Customers in the current context.

```dax
Repeat Customer Rate % =
DIVIDE ( [Repeat Customers], [Total Customers] )
```

### Orders per Customer

Average orders per active customer.

```dax
Orders per Customer =
DIVIDE ( [Total Orders], [Total Customers] )
```

### New Customers

Active customers whose first order in the dataset (DimCustomer[FirstOrderDate]) falls inside the selected dates. Data starts in Jan 2023, so 2023 counts include customers who may have bought before 2023.

```dax
New Customers =
VAR PeriodStart = MIN ( DimDate[Date] )
VAR PeriodEnd = MAX ( DimDate[Date] )
RETURN
    CALCULATE (
        [Total Customers],
        KEEPFILTERS ( DimCustomer[FirstOrderDate] >= PeriodStart && DimCustomer[FirstOrderDate] <= PeriodEnd )
    )
```

### Returning Customers

Active customers in the period who had ordered before the period started.

```dax
Returning Customers =
[Total Customers] - [New Customers]
```

## 06 Operations

| Measure | Format | Definition |
|---|---|---|
| Open Orders | `#,0` | Orders not yet shipped at the 2025-12-31 extract. |
| Average Days to Ship | `#,0.0` | Average order-to-ship days per shipped order (order-level average; open orders excluded). |
| Sales by Ship Date | `\$#,0;(\$#,0);\$#,0` | Net sales attributed to the ship date via the inactive ShipDate relationship. |

### Open Orders

Orders not yet shipped at the 2025-12-31 extract.

```dax
Open Orders =
CALCULATE ( DISTINCTCOUNT ( FactSales[OrderID] ), FactSales[OrderStatus] = "Open" )
```

### Average Days to Ship

Average order-to-ship days per shipped order (order-level average; open orders excluded).

```dax
Average Days to Ship =
AVERAGEX ( VALUES ( FactSales[OrderID] ), CALCULATE ( MAX ( FactSales[DaysToShip] ) ) )
```

### Sales by Ship Date

Net sales attributed to the ship date via the inactive ShipDate relationship.

```dax
Sales by Ship Date =
CALCULATE ( [Total Sales], USERELATIONSHIP ( FactSales[ShipDate], DimDate[Date] ) )
```

## 07 Labels & UX

| Measure | Format | Definition |
|---|---|---|
| Report Period Label | `Text` | Selected date range for page subtitles. |
| Data Through Label | `Text` | Data freshness label for the page header. |
| Selected Region Label | `Text` | Regions currently selected, or 'All regions'. |
| Selected Channel Label | `Text` | Channels currently selected, or 'All channels'. |
| Selected Category Label | `Text` | Categories currently selected, or 'All categories'. |
| Filter Context Summary | `Text` | One-line summary of the active slicers for page headers. |
| Title Monthly Sales Trend | `Text` | Dynamic title for the monthly trend visual. |
| KPI Sales Subtitle | `Text` | Subtitle for the Total Sales card showing YoY change. |
| Target Availability Note | `Text` | Explains why the target is blank at a finer filter level. |
| Growth Color | `Text` | Teal for growth, red for decline (conditional formatting on YoY visuals). |

### Report Period Label

Selected date range for page subtitles.

```dax
Report Period Label =
VAR StartDate = MIN ( DimDate[Date] )
VAR EndDate = MAX ( DimDate[Date] )
RETURN
    "Period: " & FORMAT ( StartDate, "mmm yyyy" ) & " to " & FORMAT ( EndDate, "mmm yyyy" )
```

### Data Through Label

Data freshness label for the page header.

```dax
Data Through Label =
"Data through " & FORMAT ( CALCULATE ( MAX ( FactSales[OrderDate] ), REMOVEFILTERS () ), "d mmm yyyy" )
    & "  |  Synthetic data for demonstration"
```

### Selected Region Label

Regions currently selected, or 'All regions'.

```dax
Selected Region Label =
IF (
    ISFILTERED ( DimGeography[Region] ),
    CONCATENATEX ( VALUES ( DimGeography[Region] ), DimGeography[Region], ", ", DimGeography[Region], ASC ),
    "All regions"
)
```

### Selected Channel Label

Channels currently selected, or 'All channels'.

```dax
Selected Channel Label =
IF (
    ISFILTERED ( DimSalesChannel[ChannelName] ),
    CONCATENATEX ( VALUES ( DimSalesChannel[ChannelName] ), DimSalesChannel[ChannelName], ", ", DimSalesChannel[ChannelName], ASC ),
    "All channels"
)
```

### Selected Category Label

Categories currently selected, or 'All categories'.

```dax
Selected Category Label =
IF (
    ISFILTERED ( DimProduct[Category] ),
    CONCATENATEX ( VALUES ( DimProduct[Category] ), DimProduct[Category], ", ", DimProduct[Category], ASC ),
    "All categories"
)
```

### Filter Context Summary

One-line summary of the active slicers for page headers.

```dax
Filter Context Summary =
[Selected Region Label] & "  |  " & [Selected Channel Label] & "  |  " & [Selected Category Label]
```

### Title Monthly Sales Trend

Dynamic title for the monthly trend visual.

```dax
Title Monthly Sales Trend =
"Monthly net sales vs target - " & [Selected Region Label]
```

### KPI Sales Subtitle

Subtitle for the Total Sales card showing YoY change.

```dax
KPI Sales Subtitle =
VAR g = [Sales YoY Growth %]
RETURN
    IF ( ISBLANK ( g ), "No prior-year comparison", FORMAT ( g, "+0.0%;-0.0%" ) & " vs prior year" )
```

### Target Availability Note

Explains why the target is blank at a finer filter level.

```dax
Target Availability Note =
IF (
    ISBLANK ( [Sales Target] ) && NOT ISBLANK ( [Total Sales] ),
    "Targets are set by month, region, category and channel - not available at the current filter level.",
    ""
)
```

### Growth Color

Teal for growth, red for decline (conditional formatting on YoY visuals).

```dax
Growth Color =
VAR g = [Sales YoY Growth %]
RETURN
    SWITCH ( TRUE (), ISBLANK ( g ), BLANK (), g < 0, "#C0392B", "#0F9D8A" )
```
