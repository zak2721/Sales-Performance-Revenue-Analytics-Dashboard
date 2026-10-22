# Data Dictionary

_Generated from `scripts/schema.py` by `scripts/build_powerbi_assets.py`. All data is **synthetic** and describes the fictional retailer Meridian Home & Office Co._

Files: `data/processed/<Table>.csv` (UTF-8, comma-delimited, ISO dates `YYYY-MM-DD`, logical values `true`/`false`, blank = null).

**Hidden** = hidden from report users in the Power BI model (keys, sort columns, and numeric fact columns that are exposed only through explicit measures).

| Table | Grain | Description |
|---|---|---|
| DimDate | One row per calendar day | Calendar table covering every day of 2023-2025 (full years). Mark as date table on [Date]. |
| DimProduct | One row per product | Product master with category hierarchy. |
| DimCustomer | One row per customer | Customer master enriched with segmentation attributes (as of 2025-12-31). |
| DimGeography | One row per city | Customer ship-to locations (United States). |
| DimSalesChannel | One row per channel | Sales channels. |
| FactSales | One row per OrderID + OrderLineNumber | Sales transactions at order-line grain (one row per product on an order). |
| FactSalesTarget | One row per Month x Region x Category x Channel | Monthly net-sales targets from the finance plan. |

## DimDate

Calendar table covering every day of 2023-2025 (full years). Mark as date table on [Date].  
**Grain:** One row per calendar day

| Column | Type | Hidden | Meaning | Business purpose |
|---|---|---|---|---|
| Date | Date |  | Calendar date (unique, contiguous). | Relationship key; mark-as-date-table column. |
| DateKey | Whole number | Yes | Date as YYYYMMDD integer. | Integration key for other systems. |
| Year | Whole number |  | Calendar year. | Year slicer and axis. |
| QuarterNumber | Whole number | Yes | Quarter number 1-4. | Sort key for Quarter. |
| Quarter | Text |  | Quarter label Q1-Q4. Sort by QuarterNumber. | Quarter axis and drill-down level. |
| YearQuarter | Text |  | Year and quarter, e.g. 2024-Q3. Sort by YearQuarterNumber. | Continuous quarterly trend axis. |
| YearQuarterNumber | Whole number | Yes | Year*10 + quarter, e.g. 20243. | Sort key for YearQuarter. |
| MonthNumber | Whole number | Yes | Month number 1-12. | Sort key for MonthName/MonthShort. |
| MonthName | Text |  | Full month name. Sort by MonthNumber. | Seasonality visuals. |
| MonthShort | Text |  | Three-letter month. Sort by MonthNumber. | Compact month axis labels. |
| YearMonth | Text |  | Year-month label, e.g. 2024-07. Sort by YearMonthNumber. | Continuous monthly trend axis; MoM measures check one month is in context. |
| YearMonthNumber | Whole number | Yes | Year*100 + month, e.g. 202407. | Sort key for YearMonth. |
| MonthStartDate | Date |  | First day of the month. | Monthly axis as a true date (continuous axis). |
| DayOfMonth | Whole number | Yes | Day number within the month. | Day-level analysis. |
| DayOfWeekNumber | Whole number | Yes | 1 = Monday ... 7 = Sunday. | Sort key for DayOfWeek. |
| DayOfWeek | Text |  | Weekday name. Sort by DayOfWeekNumber. | Weekday pattern analysis. |
| IsWeekend | True/False |  | TRUE for Saturday and Sunday. | Weekday vs weekend comparison. |

## DimProduct

Product master with category hierarchy.  
**Grain:** One row per product

| Column | Type | Hidden | Meaning | Business purpose |
|---|---|---|---|---|
| ProductKey | Whole number | Yes | Surrogate key. | Relationship key. |
| ProductID | Text |  | Business SKU (e.g. ELE-LAP-001). | Lookup and drill-through identifier. |
| ProductName | Text |  | Product name (unique). | Product-level analysis; Top N. |
| Category | Text |  | Product category (4 values). | Category analysis; level 1 of the product hierarchy; target grain. |
| Subcategory | Text |  | Product subcategory (16 values). | Level 2 of the product hierarchy. |
| Brand | Text |  | Fictional brand name. | Optional brand slicing. |
| ListPrice | Fixed decimal (currency) |  | Current (2025) list price in USD. | Reference only; transaction prices are in FactSales[UnitPrice]. |
| StandardCost | Fixed decimal (currency) |  | Current (2025) standard cost in USD. | Reference only; transaction costs are in FactSales[UnitCost]. |
| PriceBand | Text |  | List-price band: Under $50, $50-$199, $200-$499, $500+. Sort by PriceBandOrder. | Price-tier analysis. |
| PriceBandOrder | Whole number | Yes | Sort key for PriceBand. | Sorting. |

## DimCustomer

Customer master enriched with segmentation attributes (as of 2025-12-31).  
**Grain:** One row per customer

| Column | Type | Hidden | Meaning | Business purpose |
|---|---|---|---|---|
| CustomerKey | Whole number | Yes | Surrogate key. | Relationship key. |
| CustomerID | Text |  | Business customer ID (C-NNNNN). | Lookup and drill-through identifier. |
| CustomerName | Text |  | Fictional customer name. | Customer-level analysis; Top N. |
| Segment | Text |  | Consumer, Small Business or Corporate. | Customer segmentation by business type. |
| CustomerSince | Date |  | Account creation date from the CRM. | Customer tenure context. |
| FirstOrderDate | Date |  | First order date within the dataset (2023-2025). Blank if no orders. | New vs returning customer measures. Note: history before 2023 is not available. |
| LastOrderDate | Date |  | Most recent order date within the dataset. | Recency context. |
| LifetimeOrders | Whole number |  | Orders placed 2023-2025. | Basis for PurchaseFrequency (static). |
| LifetimeSales | Fixed decimal (currency) |  | Net sales 2023-2025. | Basis for ValueTier (static). |
| ValueTier | Text |  | A - Top 10% / B - Next 20% / C - Remaining 70% of customers by 2023-2025 net sales; 'No purchases' if none. Sort by ValueTierOrder. | Value-based segmentation (static, documented rule). |
| ValueTierOrder | Whole number | Yes | Sort key for ValueTier. | Sorting. |
| PurchaseFrequency | Text |  | One-time (1 order), Occasional (2-3), Repeat (4-9), Frequent (10+), based on 2023-2025 orders. Sort by PurchaseFrequencyOrder. | Repeat-purchase segmentation (static). |
| PurchaseFrequencyOrder | Whole number | Yes | Sort key for PurchaseFrequency. | Sorting. |

## DimGeography

Customer ship-to locations (United States).  
**Grain:** One row per city

| Column | Type | Hidden | Meaning | Business purpose |
|---|---|---|---|---|
| GeographyKey | Whole number | Yes | Surrogate key. | Relationship key. |
| Country | Text |  | Country (United States). | Map context; top of geography hierarchy. |
| Region | Text |  | Sales region: Northeast, Midwest, South, West. | Regional analysis; target grain. |
| State | Text |  | US state name. | State analysis; filled map (data category: State or Province). |
| StateCode | Text |  | Two-letter state code. | Compact labels. |
| City | Text |  | City name. | City analysis (data category: City). |
| Latitude | Decimal | Yes | City latitude. | Map placement (data category: Latitude). |
| Longitude | Decimal | Yes | City longitude. | Map placement (data category: Longitude). |

## DimSalesChannel

Sales channels.  
**Grain:** One row per channel

| Column | Type | Hidden | Meaning | Business purpose |
|---|---|---|---|---|
| ChannelKey | Whole number | Yes | Surrogate key. | Relationship key. |
| ChannelCode | Text |  | Short code: ONL, RTL, MKT, B2B. | Compact labels. |
| ChannelName | Text |  | Online Store, Retail Stores, Marketplace, B2B Wholesale. | Channel slicer and analysis. |
| ChannelType | Text |  | Direct - Digital, Direct - Physical, Third-Party, Wholesale. | Channel grouping. |

## FactSales

Sales transactions at order-line grain (one row per product on an order).  
**Grain:** One row per OrderID + OrderLineNumber

| Column | Type | Hidden | Meaning | Business purpose |
|---|---|---|---|---|
| SalesLineID | Whole number | Yes | Surrogate key for the order line. | Unique row identifier; supports reconciliation. |
| OrderID | Text |  | Business order number (SO-YYYY-NNNNNN). | Counting orders (DISTINCTCOUNT) and order-level analysis. |
| OrderLineNumber | Whole number | Yes | Line number within the order. | Identifies a product line within an order. |
| OrderDate | Date | Yes | Date the order was placed. | Active relationship to DimDate; drives all time analysis. |
| ShipDate | Date | Yes | Date the order shipped. Blank when OrderStatus = Open. | Inactive relationship to DimDate for ship-date analysis; fulfilment speed. |
| OrderStatus | Text |  | Shipped or Open (not shipped by the extract date 2025-12-31). | Explains blank ship dates; open-order monitoring. |
| DaysToShip | Whole number |  | ShipDate minus OrderDate in days. Blank for open orders. | Fulfilment speed by channel. |
| CustomerKey | Whole number | Yes | Foreign key to DimCustomer. | Relationship key. |
| ProductKey | Whole number | Yes | Foreign key to DimProduct. | Relationship key. |
| GeographyKey | Whole number | Yes | Foreign key to DimGeography (customer ship-to city). | Relationship key. |
| ChannelKey | Whole number | Yes | Foreign key to DimSalesChannel. | Relationship key. |
| Quantity | Whole number | Yes | Units sold on the line. | Units sold; average selling price. |
| UnitPrice | Fixed decimal (currency) | Yes | List price per unit at time of sale, before discount (USD). | Gross sales calculation; price analysis. |
| UnitCost | Fixed decimal (currency) | Yes | Standard cost per unit at time of sale (USD). | Cost calculation. |
| DiscountPct | Percentage | Yes | Line discount as a fraction of gross sales (0.15 = 15%). | Discount analysis (use the Discount Rate % measure for aggregates). |
| DiscountBand | Text |  | Discount bucket: No discount, 1-10%, 11-20%, 21-30%, 31-40%. Sort by DiscountBandOrder. | Axis for discount-versus-margin analysis. |
| DiscountBandOrder | Whole number | Yes | Sort key for DiscountBand. | Sorting. |
| GrossSales | Fixed decimal (currency) | Yes | Quantity x UnitPrice (before discount). | Denominator for discount rate; list-margin analysis. |
| DiscountAmount | Fixed decimal (currency) | Yes | GrossSales x DiscountPct, rounded to cents. | Discount Amount measure. |
| SalesAmount | Fixed decimal (currency) | Yes | Net sales = GrossSales - DiscountAmount. This is 'Sales' / revenue throughout the report. | Total Sales measure and all revenue KPIs. |
| CostAmount | Fixed decimal (currency) | Yes | Quantity x UnitCost. | Total Cost measure. |
| Profit | Fixed decimal (currency) | Yes | SalesAmount - CostAmount (gross profit after discount, before overheads). | Total Profit and margin measures. |

## FactSalesTarget

Monthly net-sales targets from the finance plan.  
**Grain:** One row per Month x Region x Category x Channel

| Column | Type | Hidden | Meaning | Business purpose |
|---|---|---|---|---|
| TargetID | Whole number | Yes | Surrogate key. | Unique row identifier. |
| TargetMonth | Date | Yes | First day of the target month. | Relationship to DimDate[Date]. |
| Region | Text | Yes | Sales region (matches DimGeography[Region]). | Applied through TREATAS in the Sales Target measure. |
| Category | Text | Yes | Product category (matches DimProduct[Category]). | Applied through TREATAS in the Sales Target measure. |
| ChannelKey | Whole number | Yes | Foreign key to DimSalesChannel. | Relationship key. |
| TargetAmount | Fixed decimal (currency) | Yes | Net-sales target in USD. | Sales Target measure. |

## Calculation rules

| Field | Formula | Notes |
|---|---|---|
| GrossSales | Quantity x UnitPrice | Rounded to cents |
| DiscountAmount | GrossSales x DiscountPct | Rounded to cents. Discount is applied **before** revenue is recognised |
| SalesAmount (net sales, 'Sales') | GrossSales - DiscountAmount | Revenue used in every KPI |
| CostAmount | Quantity x UnitCost | Standard cost at time of sale |
| Profit | SalesAmount - CostAmount | Gross profit; no overheads, freight or returns |
| DaysToShip | ShipDate - OrderDate | Blank for open orders |
