"""
DAX measure library - single source of truth.

build_powerbi_assets.py turns this list into:
  * powerbi/dax_measures.md           (documentation)
  * powerbi/tmdl/measures.tmdl        (TMDL script to paste into Power BI Desktop's TMDL view)

All measures live in a dedicated measure table named `_Measures`, organised by display folder.
"""

CUR0 = r"\$#,0;(\$#,0);\$#,0"
CUR2 = r"\$#,0.00;(\$#,0.00);\$#,0.00"
INT = "#,0"
DEC1 = "#,0.0"
PCT1 = "0.0%;-0.0%;0.0%"

RED, AMBER, TEAL, SLATE = "#C0392B", "#E08E0B", "#0F9D8A", "#94A3B8"

MEASURES = [
    # ------------------------------------------------------------------ 01 Sales
    ("Total Sales", "01 Sales", CUR0,
     "Net sales (revenue after line discounts). The 'Sales' figure used everywhere in the report.",
     "SUM ( FactSales[SalesAmount] )"),
    ("Gross Sales", "01 Sales", CUR0,
     "Sales at list price before discounts (Quantity x UnitPrice).",
     "SUM ( FactSales[GrossSales] )"),
    ("Total Orders", "01 Sales", INT,
     "Number of distinct orders.",
     "DISTINCTCOUNT ( FactSales[OrderID] )"),
    ("Total Order Lines", "01 Sales", INT,
     "Number of order lines (fact rows).",
     "COUNTROWS ( FactSales )"),
    ("Total Units Sold", "01 Sales", INT,
     "Units sold.",
     "SUM ( FactSales[Quantity] )"),
    ("Total Customers", "01 Sales", INT,
     "Distinct customers who placed at least one order in the current filter context.",
     "DISTINCTCOUNT ( FactSales[CustomerKey] )"),
    ("Average Order Value", "01 Sales", CUR2,
     "Net sales per order.",
     "DIVIDE ( [Total Sales], [Total Orders] )"),
    ("Average Selling Price", "01 Sales", CUR2,
     "Net sales per unit (after discount).",
     "DIVIDE ( [Total Sales], [Total Units Sold] )"),
    ("Sales per Customer", "01 Sales", CUR0,
     "Net sales per active customer.",
     "DIVIDE ( [Total Sales], [Total Customers] )"),

    # ------------------------------------------------------------------ 02 Profitability
    ("Total Cost", "02 Profitability", CUR0,
     "Cost of goods sold (Quantity x UnitCost).",
     "SUM ( FactSales[CostAmount] )"),
    ("Total Profit", "02 Profitability", CUR0,
     "Gross profit after discounts = Net sales - Cost. Excludes overheads, shipping and returns (not in the data).",
     "SUM ( FactSales[Profit] )"),
    ("Profit Margin %", "02 Profitability", PCT1,
     "Total Profit / Total Sales (ratio of sums, never an average of line margins).",
     "DIVIDE ( [Total Profit], [Total Sales] )"),
    ("Average Profit per Order", "02 Profitability", CUR2,
     "Gross profit per order.",
     "DIVIDE ( [Total Profit], [Total Orders] )"),
    ("Discount Amount", "02 Profitability", CUR0,
     "Value of discounts given (Gross Sales - Net Sales).",
     "SUM ( FactSales[DiscountAmount] )"),
    ("Discount Rate %", "02 Profitability", PCT1,
     "Discount Amount / Gross Sales. Effective discount rate on list-price sales.",
     "DIVIDE ( [Discount Amount], [Gross Sales] )"),
    ("List Margin %", "02 Profitability", PCT1,
     "Margin the same sales would have earned at list price: (Gross Sales - Cost) / Gross Sales.",
     "DIVIDE ( [Gross Sales] - [Total Cost], [Gross Sales] )"),
    ("Margin Erosion from Discounts", "02 Profitability", PCT1,
     "List Margin % minus Profit Margin %, in percentage points. Arithmetic effect of discounts on margin, "
     "holding volume constant - not an estimate of what would have sold without the discount.",
     "IF ( NOT ISBLANK ( [Total Sales] ), [List Margin %] - [Profit Margin %] )"),
    ("Discounted Sales Share %", "02 Profitability", PCT1,
     "Share of net sales that came from discounted lines.",
     "DIVIDE ( CALCULATE ( [Total Sales], FactSales[DiscountPct] > 0 ), [Total Sales] )"),
    ("Profit Margin % (Full-Price Lines)", "02 Profitability", PCT1,
     "Profit margin on lines sold without a discount.",
     "CALCULATE ( [Profit Margin %], FactSales[DiscountPct] = 0 )"),
    ("Profit Margin % (Discounted Lines)", "02 Profitability", PCT1,
     "Profit margin on lines sold with any discount.",
     "CALCULATE ( [Profit Margin %], FactSales[DiscountPct] > 0 )"),
    ("Loss-Making Lines", "02 Profitability", INT,
     "Order lines with negative profit.",
     "CALCULATE ( COUNTROWS ( FactSales ), FactSales[Profit] < 0 )"),
    ("Loss-Making Sales", "02 Profitability", CUR0,
     "Net sales on order lines with negative profit.",
     "CALCULATE ( [Total Sales], FactSales[Profit] < 0 )"),
    ("Loss on Loss-Making Lines", "02 Profitability", CUR0,
     "Total (negative) profit on loss-making order lines.",
     "CALCULATE ( [Total Profit], FactSales[Profit] < 0 )"),
    ("Products with Negative Profit", "02 Profitability", INT,
     "Number of products whose total profit is negative in the current context.",
     "COUNTROWS ( FILTER ( VALUES ( DimProduct[ProductKey] ), [Total Profit] < 0 ) )"),
    ("Margin Status", "02 Profitability", None,
     "Margin band used for conditional formatting and tooltips. Thresholds: <0% Loss, <15% Low, <30% Moderate, otherwise Healthy.",
     """VAR m = [Profit Margin %]
RETURN
    SWITCH (
        TRUE (),
        ISBLANK ( m ), BLANK (),
        m < 0, "Loss",
        m < 0.15, "Low (<15%)",
        m < 0.30, "Moderate (15-30%)",
        "Healthy (30%+)"
    )"""),
    ("Margin Status Color", "02 Profitability", None,
     "Hex colour for conditional formatting (Format > Conditional formatting > Field value).",
     f"""VAR m = [Profit Margin %]
RETURN
    SWITCH (
        TRUE (),
        ISBLANK ( m ), BLANK (),
        m < 0, "{RED}",
        m < 0.15, "{AMBER}",
        m < 0.30, "{SLATE}",
        "{TEAL}"
    )"""),

    # ------------------------------------------------------------------ 03 Time Intelligence
    ("Sales Previous Month", "03 Time Intelligence", CUR0,
     "Net sales in the previous month. Returns blank unless exactly one month is in context.",
     """IF (
    HASONEVALUE ( DimDate[YearMonth] ),
    CALCULATE ( [Total Sales], DATEADD ( DimDate[Date], -1, MONTH ) )
)"""),
    ("Sales MoM Change", "03 Time Intelligence", CUR0,
     "Net sales minus previous month. Blank when either month has no data (e.g. Jan 2023).",
     """VAR CurrentSales = [Total Sales]
VAR PreviousSales = [Sales Previous Month]
RETURN
    IF ( NOT ISBLANK ( CurrentSales ) && NOT ISBLANK ( PreviousSales ), CurrentSales - PreviousSales )"""),
    ("Sales MoM Growth %", "03 Time Intelligence", PCT1,
     "Month-over-month growth in net sales.",
     "DIVIDE ( [Sales MoM Change], [Sales Previous Month] )"),
    ("Sales Previous Year", "03 Time Intelligence", CUR0,
     "Net sales in the same period one year earlier.",
     "CALCULATE ( [Total Sales], SAMEPERIODLASTYEAR ( DimDate[Date] ) )"),
    ("Sales YoY Change", "03 Time Intelligence", CUR0,
     "Net sales minus the same period last year. Blank when there is no prior-year data (all of 2023).",
     """VAR CurrentSales = [Total Sales]
VAR PriorSales = [Sales Previous Year]
RETURN
    IF ( NOT ISBLANK ( CurrentSales ) && NOT ISBLANK ( PriorSales ), CurrentSales - PriorSales )"""),
    ("Sales YoY Growth %", "03 Time Intelligence", PCT1,
     "Year-over-year growth in net sales.",
     "DIVIDE ( [Sales YoY Change], [Sales Previous Year] )"),
    ("Sales YTD", "03 Time Intelligence", CUR0,
     "Year-to-date net sales (calendar year) up to the last date in context.",
     "CALCULATE ( [Total Sales], DATESYTD ( DimDate[Date] ) )"),
    ("Sales PYTD", "03 Time Intelligence", CUR0,
     "Prior-year-to-date net sales (same calendar dates one year earlier).",
     "CALCULATE ( [Sales YTD], SAMEPERIODLASTYEAR ( DimDate[Date] ) )"),
    ("Sales YTD Growth %", "03 Time Intelligence", PCT1,
     "YTD net sales vs prior YTD.",
     """VAR ytd = [Sales YTD]
VAR pytd = [Sales PYTD]
RETURN
    IF ( NOT ISBLANK ( ytd ) && NOT ISBLANK ( pytd ), DIVIDE ( ytd - pytd, pytd ) )"""),
    ("Profit YTD", "03 Time Intelligence", CUR0,
     "Year-to-date gross profit.",
     "CALCULATE ( [Total Profit], DATESYTD ( DimDate[Date] ) )"),
    ("Profit Previous Year", "03 Time Intelligence", CUR0,
     "Gross profit in the same period one year earlier.",
     "CALCULATE ( [Total Profit], SAMEPERIODLASTYEAR ( DimDate[Date] ) )"),
    ("Profit YoY Growth %", "03 Time Intelligence", PCT1,
     "Year-over-year growth in gross profit.",
     """VAR CurrentProfit = [Total Profit]
VAR PriorProfit = [Profit Previous Year]
RETURN
    IF ( NOT ISBLANK ( CurrentProfit ) && NOT ISBLANK ( PriorProfit ), DIVIDE ( CurrentProfit - PriorProfit, ABS ( PriorProfit ) ) )"""),
    ("Orders YoY Growth %", "03 Time Intelligence", PCT1,
     "Year-over-year growth in order count.",
     """VAR CurrentOrders = [Total Orders]
VAR PriorOrders = CALCULATE ( [Total Orders], SAMEPERIODLASTYEAR ( DimDate[Date] ) )
RETURN
    IF ( NOT ISBLANK ( CurrentOrders ) && NOT ISBLANK ( PriorOrders ), DIVIDE ( CurrentOrders - PriorOrders, PriorOrders ) )"""),
    ("AOV YoY Growth %", "03 Time Intelligence", PCT1,
     "Year-over-year change in average order value.",
     """VAR CurrentAOV = [Average Order Value]
VAR PriorAOV = CALCULATE ( [Average Order Value], SAMEPERIODLASTYEAR ( DimDate[Date] ) )
RETURN
    IF ( NOT ISBLANK ( CurrentAOV ) && NOT ISBLANK ( PriorAOV ), DIVIDE ( CurrentAOV - PriorAOV, PriorAOV ) )"""),
    ("Sales Rolling 3M Avg", "03 Time Intelligence", CUR0,
     "Average monthly net sales over the 3 months ending at the last date in context. Blank until 3 full months exist.",
     """VAR LastDate = MAX ( DimDate[Date] )
VAR Period = DATESINPERIOD ( DimDate[Date], LastDate, -3, MONTH )
VAR MonthsInPeriod = CALCULATE ( DISTINCTCOUNT ( DimDate[YearMonth] ), Period )
RETURN
    IF ( MonthsInPeriod = 3, DIVIDE ( CALCULATE ( [Total Sales], Period ), 3 ) )"""),

    # ------------------------------------------------------------------ 04 Targets
    ("Sales Target", "04 Targets", CUR0,
     "Net-sales target from the finance plan. Targets exist at Month x Region x Category x Channel. "
     "Region and Category are applied with TREATAS; month and channel through physical relationships. "
     "Returns blank when the report is filtered below target grain (state/city, subcategory/product/brand/price band, "
     "or any customer attribute) because no target exists at that level.",
     """VAR VisibleProducts = COUNTROWS ( VALUES ( DimProduct[ProductKey] ) )
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
    )"""),
    ("Sales vs Target", "04 Targets", CUR0,
     "Net sales minus target (positive = ahead of target).",
     """VAR TargetValue = [Sales Target]
RETURN
    IF ( NOT ISBLANK ( TargetValue ), [Total Sales] - TargetValue )"""),
    ("Target Achievement %", "04 Targets", PCT1,
     "Net sales / target.",
     "DIVIDE ( [Total Sales], [Sales Target] )"),
    ("Remaining Sales to Target", "04 Targets", CUR0,
     "Sales still needed to reach target; zero once the target is met.",
     """VAR TargetValue = [Sales Target]
RETURN
    IF ( NOT ISBLANK ( TargetValue ), MAX ( 0, TargetValue - [Total Sales] ) )"""),
    ("Sales Target YTD", "04 Targets", CUR0,
     "Year-to-date target.",
     "CALCULATE ( [Sales Target], DATESYTD ( DimDate[Date] ) )"),
    ("Target Achievement % YTD", "04 Targets", PCT1,
     "YTD net sales / YTD target.",
     "DIVIDE ( [Sales YTD], [Sales Target YTD] )"),
    ("Target Status", "04 Targets", None,
     "On target (>=100%), Near target (95-99.9%), Below target (<95%).",
     """VAR a = [Target Achievement %]
RETURN
    SWITCH ( TRUE (), ISBLANK ( a ), BLANK (), a >= 1, "On target", a >= 0.95, "Near target", "Below target" )"""),
    ("Target Status Color", "04 Targets", None,
     "Hex colour for conditional formatting of target achievement.",
     f"""VAR a = [Target Achievement %]
RETURN
    SWITCH ( TRUE (), ISBLANK ( a ), BLANK (), a >= 1, "{TEAL}", a >= 0.95, "{AMBER}", "{RED}" )"""),

    # ------------------------------------------------------------------ 05 Product & Customer
    ("Product Sales Contribution %", "05 Product & Customer", PCT1,
     "Share of net sales within the products selected by slicers (ALLSELECTED). In a product table, rows sum to 100%.",
     "DIVIDE ( [Total Sales], CALCULATE ( [Total Sales], ALLSELECTED ( DimProduct ) ) )"),
    ("Category Sales Contribution %", "05 Product & Customer", PCT1,
     "Share of the current row's category in selected net sales. At subcategory/product level it returns the parent category's share.",
     """VAR CategorySales =
    CALCULATE ( [Total Sales], ALLSELECTED ( DimProduct ), VALUES ( DimProduct[Category] ) )
VAR SelectedSales = CALCULATE ( [Total Sales], ALLSELECTED ( DimProduct ) )
RETURN
    DIVIDE ( CategorySales, SelectedSales )"""),
    ("Customer Sales Contribution %", "05 Product & Customer", PCT1,
     "Share of net sales within the customers selected by slicers.",
     "DIVIDE ( [Total Sales], CALCULATE ( [Total Sales], ALLSELECTED ( DimCustomer ) ) )"),
    ("Product Sales Rank", "05 Product & Customer", INT,
     "Rank of a product by net sales among selected products (1 = highest). Use with a Top N visual filter.",
     """IF (
    ISINSCOPE ( DimProduct[ProductName] ) && NOT ISBLANK ( [Total Sales] ),
    RANKX ( ALLSELECTED ( DimProduct[ProductName] ), [Total Sales], , DESC, DENSE )
)"""),
    ("Product Profit Rank (Lowest First)", "05 Product & Customer", INT,
     "Rank of products by profit, lowest first, ignoring products with no sales. Use to list bottom performers.",
     """IF (
    ISINSCOPE ( DimProduct[ProductName] ) && NOT ISBLANK ( [Total Sales] ),
    RANKX (
        FILTER ( ALLSELECTED ( DimProduct[ProductName] ), NOT ISBLANK ( [Total Sales] ) ),
        [Total Profit], , ASC, DENSE
    )
)"""),
    ("Customer Sales Rank", "05 Product & Customer", INT,
     "Rank of a customer by net sales among selected customers.",
     """IF (
    ISINSCOPE ( DimCustomer[CustomerName] ) && NOT ISBLANK ( [Total Sales] ),
    RANKX ( ALLSELECTED ( DimCustomer[CustomerName] ), [Total Sales], , DESC, DENSE )
)"""),
    ("Top Product by Sales", "05 Product & Customer", None,
     "Name of the highest-selling product in the current context (for cards and titles).",
     """VAR TopProduct = TOPN ( 1, VALUES ( DimProduct[ProductName] ), [Total Sales], DESC )
RETURN
    IF ( NOT ISBLANK ( [Total Sales] ), CONCATENATEX ( TopProduct, DimProduct[ProductName], ", " ) )"""),
    ("Top Customer by Sales", "05 Product & Customer", None,
     "Name of the highest-spending customer in the current context.",
     """VAR TopCustomer = TOPN ( 1, VALUES ( DimCustomer[CustomerName] ), [Total Sales], DESC )
RETURN
    IF ( NOT ISBLANK ( [Total Sales] ), CONCATENATEX ( TopCustomer, DimCustomer[CustomerName], ", " ) )"""),
    ("Top 10 Products Sales Share %", "05 Product & Customer", PCT1,
     "Share of net sales generated by the 10 highest-selling products in the current context (concentration).",
     """VAR Top10 = TOPN ( 10, VALUES ( DimProduct[ProductName] ), [Total Sales], DESC )
RETURN
    DIVIDE ( CALCULATE ( [Total Sales], Top10 ), [Total Sales] )"""),
    ("Top 10 Customers Sales Share %", "05 Product & Customer", PCT1,
     "Share of net sales from the 10 highest-spending customers in the current context.",
     """VAR Top10 = TOPN ( 10, VALUES ( DimCustomer[CustomerKey] ), [Total Sales], DESC )
RETURN
    DIVIDE ( CALCULATE ( [Total Sales], Top10 ), [Total Sales] )"""),
    ("Top 20% Customers Sales Share %", "05 Product & Customer", PCT1,
     "Share of net sales from the top 20% of purchasing customers (Pareto check).",
     """VAR Buyers = FILTER ( VALUES ( DimCustomer[CustomerKey] ), NOT ISBLANK ( [Total Sales] ) )
VAR TopCount = ROUNDUP ( COUNTROWS ( Buyers ) * 0.2, 0 )
VAR TopCustomers = TOPN ( TopCount, Buyers, [Total Sales], DESC )
RETURN
    DIVIDE ( CALCULATE ( [Total Sales], TopCustomers ), [Total Sales] )"""),
    ("Repeat Customers", "05 Product & Customer", INT,
     "Customers with 2 or more orders within the current filter context (period, channel, etc.).",
     """COUNTROWS (
    FILTER ( VALUES ( FactSales[CustomerKey] ), CALCULATE ( DISTINCTCOUNT ( FactSales[OrderID] ) ) >= 2 )
)"""),
    ("Repeat Customer Rate %", "05 Product & Customer", PCT1,
     "Repeat Customers / Total Customers in the current context.",
     "DIVIDE ( [Repeat Customers], [Total Customers] )"),
    ("Orders per Customer", "05 Product & Customer", DEC1,
     "Average orders per active customer.",
     "DIVIDE ( [Total Orders], [Total Customers] )"),
    ("New Customers", "05 Product & Customer", INT,
     "Active customers whose first order in the dataset (DimCustomer[FirstOrderDate]) falls inside the selected dates. "
     "Data starts in Jan 2023, so 2023 counts include customers who may have bought before 2023.",
     """VAR PeriodStart = MIN ( DimDate[Date] )
VAR PeriodEnd = MAX ( DimDate[Date] )
RETURN
    CALCULATE (
        [Total Customers],
        KEEPFILTERS ( DimCustomer[FirstOrderDate] >= PeriodStart && DimCustomer[FirstOrderDate] <= PeriodEnd )
    )"""),
    ("Returning Customers", "05 Product & Customer", INT,
     "Active customers in the period who had ordered before the period started.",
     "[Total Customers] - [New Customers]"),

    # ------------------------------------------------------------------ 06 Operations
    ("Open Orders", "06 Operations", INT,
     "Orders not yet shipped at the 2025-12-31 extract.",
     """CALCULATE ( DISTINCTCOUNT ( FactSales[OrderID] ), FactSales[OrderStatus] = "Open" )"""),
    ("Average Days to Ship", "06 Operations", DEC1,
     "Average order-to-ship days per shipped order (order-level average; open orders excluded).",
     "AVERAGEX ( VALUES ( FactSales[OrderID] ), CALCULATE ( MAX ( FactSales[DaysToShip] ) ) )"),
    ("Sales by Ship Date", "06 Operations", CUR0,
     "Net sales attributed to the ship date via the inactive ShipDate relationship.",
     "CALCULATE ( [Total Sales], USERELATIONSHIP ( FactSales[ShipDate], DimDate[Date] ) )"),

    # ------------------------------------------------------------------ 07 Labels & UX
    ("Report Period Label", "07 Labels & UX", None,
     "Selected date range for page subtitles.",
     """VAR StartDate = MIN ( DimDate[Date] )
VAR EndDate = MAX ( DimDate[Date] )
RETURN
    "Period: " & FORMAT ( StartDate, "mmm yyyy" ) & " to " & FORMAT ( EndDate, "mmm yyyy" )"""),
    ("Data Through Label", "07 Labels & UX", None,
     "Data freshness label for the page header.",
     """"Data through " & FORMAT ( CALCULATE ( MAX ( FactSales[OrderDate] ), REMOVEFILTERS () ), "d mmm yyyy" )
    & "  |  Synthetic data for demonstration\""""),
    ("Selected Region Label", "07 Labels & UX", None,
     "Regions currently selected, or 'All regions'.",
     """IF (
    ISFILTERED ( DimGeography[Region] ),
    CONCATENATEX ( VALUES ( DimGeography[Region] ), DimGeography[Region], ", ", DimGeography[Region], ASC ),
    "All regions"
)"""),
    ("Selected Channel Label", "07 Labels & UX", None,
     "Channels currently selected, or 'All channels'.",
     """IF (
    ISFILTERED ( DimSalesChannel[ChannelName] ),
    CONCATENATEX ( VALUES ( DimSalesChannel[ChannelName] ), DimSalesChannel[ChannelName], ", ", DimSalesChannel[ChannelName], ASC ),
    "All channels"
)"""),
    ("Selected Category Label", "07 Labels & UX", None,
     "Categories currently selected, or 'All categories'.",
     """IF (
    ISFILTERED ( DimProduct[Category] ),
    CONCATENATEX ( VALUES ( DimProduct[Category] ), DimProduct[Category], ", ", DimProduct[Category], ASC ),
    "All categories"
)"""),
    ("Filter Context Summary", "07 Labels & UX", None,
     "One-line summary of the active slicers for page headers.",
     """[Selected Region Label] & "  |  " & [Selected Channel Label] & "  |  " & [Selected Category Label]"""),
    ("Title Monthly Sales Trend", "07 Labels & UX", None,
     "Dynamic title for the monthly trend visual.",
     """"Monthly net sales vs target - " & [Selected Region Label]"""),
    ("KPI Sales Subtitle", "07 Labels & UX", None,
     "Subtitle for the Total Sales card showing YoY change.",
     """VAR g = [Sales YoY Growth %]
RETURN
    IF ( ISBLANK ( g ), "No prior-year comparison", FORMAT ( g, "+0.0%;-0.0%" ) & " vs prior year" )"""),
    ("Target Availability Note", "07 Labels & UX", None,
     "Explains why the target is blank at a finer filter level.",
     """IF (
    ISBLANK ( [Sales Target] ) && NOT ISBLANK ( [Total Sales] ),
    "Targets are set by month, region, category and channel - not available at the current filter level.",
    ""
)"""),
    ("Growth Color", "07 Labels & UX", None,
     "Teal for growth, red for decline (conditional formatting on YoY visuals).",
     f"""VAR g = [Sales YoY Growth %]
RETURN
    SWITCH ( TRUE (), ISBLANK ( g ), BLANK (), g < 0, "{RED}", "{TEAL}" )"""),
]
