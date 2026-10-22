"""
Single source of truth for the processed star schema.

Used by:
  * prepare_data.py           - enforces column order of the processed CSVs
  * build_powerbi_assets.py   - generates Power Query (M) scripts and docs/data_dictionary.md
  * tests/data_quality_checks.py - checks the CSVs match this schema exactly

Types are Power Query types: "Int64.Type", "type text", "type date", "Currency.Type",
"type number", "Percentage.Type", "type logical".
"""

# table -> description, grain, columns: (name, pq_type, description, business purpose, hidden_in_report)
SCHEMA = {
    "FactSales": {
        "description": "Sales transactions at order-line grain (one row per product on an order).",
        "grain": "One row per OrderID + OrderLineNumber",
        "columns": [
            ("SalesLineID", "Int64.Type", "Surrogate key for the order line.", "Unique row identifier; supports reconciliation.", True),
            ("OrderID", "type text", "Business order number (SO-YYYY-NNNNNN).", "Counting orders (DISTINCTCOUNT) and order-level analysis.", False),
            ("OrderLineNumber", "Int64.Type", "Line number within the order.", "Identifies a product line within an order.", True),
            ("OrderDate", "type date", "Date the order was placed.", "Active relationship to DimDate; drives all time analysis.", True),
            ("ShipDate", "type date", "Date the order shipped. Blank when OrderStatus = Open.", "Inactive relationship to DimDate for ship-date analysis; fulfilment speed.", True),
            ("OrderStatus", "type text", "Shipped or Open (not shipped by the extract date 2025-12-31).", "Explains blank ship dates; open-order monitoring.", False),
            ("DaysToShip", "Int64.Type", "ShipDate minus OrderDate in days. Blank for open orders.", "Fulfilment speed by channel.", False),
            ("CustomerKey", "Int64.Type", "Foreign key to DimCustomer.", "Relationship key.", True),
            ("ProductKey", "Int64.Type", "Foreign key to DimProduct.", "Relationship key.", True),
            ("GeographyKey", "Int64.Type", "Foreign key to DimGeography (customer ship-to city).", "Relationship key.", True),
            ("ChannelKey", "Int64.Type", "Foreign key to DimSalesChannel.", "Relationship key.", True),
            ("Quantity", "Int64.Type", "Units sold on the line.", "Units sold; average selling price.", True),
            ("UnitPrice", "Currency.Type", "List price per unit at time of sale, before discount (USD).", "Gross sales calculation; price analysis.", True),
            ("UnitCost", "Currency.Type", "Standard cost per unit at time of sale (USD).", "Cost calculation.", True),
            ("DiscountPct", "Percentage.Type", "Line discount as a fraction of gross sales (0.15 = 15%).", "Discount analysis (use the Discount Rate % measure for aggregates).", True),
            ("DiscountBand", "type text", "Discount bucket: No discount, 1-10%, 11-20%, 21-30%, 31-40%. Sort by DiscountBandOrder.", "Axis for discount-versus-margin analysis.", False),
            ("DiscountBandOrder", "Int64.Type", "Sort key for DiscountBand.", "Sorting.", True),
            ("GrossSales", "Currency.Type", "Quantity x UnitPrice (before discount).", "Denominator for discount rate; list-margin analysis.", True),
            ("DiscountAmount", "Currency.Type", "GrossSales x DiscountPct, rounded to cents.", "Discount Amount measure.", True),
            ("SalesAmount", "Currency.Type", "Net sales = GrossSales - DiscountAmount. This is 'Sales' / revenue throughout the report.", "Total Sales measure and all revenue KPIs.", True),
            ("CostAmount", "Currency.Type", "Quantity x UnitCost.", "Total Cost measure.", True),
            ("Profit", "Currency.Type", "SalesAmount - CostAmount (gross profit after discount, before overheads).", "Total Profit and margin measures.", True),
        ],
    },
    "DimDate": {
        "description": "Calendar table covering every day of 2023-2025 (full years). Mark as date table on [Date].",
        "grain": "One row per calendar day",
        "columns": [
            ("Date", "type date", "Calendar date (unique, contiguous).", "Relationship key; mark-as-date-table column.", False),
            ("DateKey", "Int64.Type", "Date as YYYYMMDD integer.", "Integration key for other systems.", True),
            ("Year", "Int64.Type", "Calendar year.", "Year slicer and axis.", False),
            ("QuarterNumber", "Int64.Type", "Quarter number 1-4.", "Sort key for Quarter.", True),
            ("Quarter", "type text", "Quarter label Q1-Q4. Sort by QuarterNumber.", "Quarter axis and drill-down level.", False),
            ("YearQuarter", "type text", "Year and quarter, e.g. 2024-Q3. Sort by YearQuarterNumber.", "Continuous quarterly trend axis.", False),
            ("YearQuarterNumber", "Int64.Type", "Year*10 + quarter, e.g. 20243.", "Sort key for YearQuarter.", True),
            ("MonthNumber", "Int64.Type", "Month number 1-12.", "Sort key for MonthName/MonthShort.", True),
            ("MonthName", "type text", "Full month name. Sort by MonthNumber.", "Seasonality visuals.", False),
            ("MonthShort", "type text", "Three-letter month. Sort by MonthNumber.", "Compact month axis labels.", False),
            ("YearMonth", "type text", "Year-month label, e.g. 2024-07. Sort by YearMonthNumber.", "Continuous monthly trend axis; MoM measures check one month is in context.", False),
            ("YearMonthNumber", "Int64.Type", "Year*100 + month, e.g. 202407.", "Sort key for YearMonth.", True),
            ("MonthStartDate", "type date", "First day of the month.", "Monthly axis as a true date (continuous axis).", False),
            ("DayOfMonth", "Int64.Type", "Day number within the month.", "Day-level analysis.", True),
            ("DayOfWeekNumber", "Int64.Type", "1 = Monday ... 7 = Sunday.", "Sort key for DayOfWeek.", True),
            ("DayOfWeek", "type text", "Weekday name. Sort by DayOfWeekNumber.", "Weekday pattern analysis.", False),
            ("IsWeekend", "type logical", "TRUE for Saturday and Sunday.", "Weekday vs weekend comparison.", False),
        ],
    },
    "DimProduct": {
        "description": "Product master with category hierarchy.",
        "grain": "One row per product",
        "columns": [
            ("ProductKey", "Int64.Type", "Surrogate key.", "Relationship key.", True),
            ("ProductID", "type text", "Business SKU (e.g. ELE-LAP-001).", "Lookup and drill-through identifier.", False),
            ("ProductName", "type text", "Product name (unique).", "Product-level analysis; Top N.", False),
            ("Category", "type text", "Product category (4 values).", "Category analysis; level 1 of the product hierarchy; target grain.", False),
            ("Subcategory", "type text", "Product subcategory (16 values).", "Level 2 of the product hierarchy.", False),
            ("Brand", "type text", "Fictional brand name.", "Optional brand slicing.", False),
            ("ListPrice", "Currency.Type", "Current (2025) list price in USD.", "Reference only; transaction prices are in FactSales[UnitPrice].", False),
            ("StandardCost", "Currency.Type", "Current (2025) standard cost in USD.", "Reference only; transaction costs are in FactSales[UnitCost].", False),
            ("PriceBand", "type text", "List-price band: Under $50, $50-$199, $200-$499, $500+. Sort by PriceBandOrder.", "Price-tier analysis.", False),
            ("PriceBandOrder", "Int64.Type", "Sort key for PriceBand.", "Sorting.", True),
        ],
    },
    "DimCustomer": {
        "description": "Customer master enriched with segmentation attributes (as of 2025-12-31).",
        "grain": "One row per customer",
        "columns": [
            ("CustomerKey", "Int64.Type", "Surrogate key.", "Relationship key.", True),
            ("CustomerID", "type text", "Business customer ID (C-NNNNN).", "Lookup and drill-through identifier.", False),
            ("CustomerName", "type text", "Fictional customer name.", "Customer-level analysis; Top N.", False),
            ("Segment", "type text", "Consumer, Small Business or Corporate.", "Customer segmentation by business type.", False),
            ("CustomerSince", "type date", "Account creation date from the CRM.", "Customer tenure context.", False),
            ("FirstOrderDate", "type date", "First order date within the dataset (2023-2025). Blank if no orders.", "New vs returning customer measures. Note: history before 2023 is not available.", False),
            ("LastOrderDate", "type date", "Most recent order date within the dataset.", "Recency context.", False),
            ("LifetimeOrders", "Int64.Type", "Orders placed 2023-2025.", "Basis for PurchaseFrequency (static).", False),
            ("LifetimeSales", "Currency.Type", "Net sales 2023-2025.", "Basis for ValueTier (static).", False),
            ("ValueTier", "type text", "A - Top 10% / B - Next 20% / C - Remaining 70% of customers by 2023-2025 net sales; 'No purchases' if none. Sort by ValueTierOrder.", "Value-based segmentation (static, documented rule).", False),
            ("ValueTierOrder", "Int64.Type", "Sort key for ValueTier.", "Sorting.", True),
            ("PurchaseFrequency", "type text", "One-time (1 order), Occasional (2-3), Repeat (4-9), Frequent (10+), based on 2023-2025 orders. Sort by PurchaseFrequencyOrder.", "Repeat-purchase segmentation (static).", False),
            ("PurchaseFrequencyOrder", "Int64.Type", "Sort key for PurchaseFrequency.", "Sorting.", True),
        ],
    },
    "DimGeography": {
        "description": "Customer ship-to locations (United States).",
        "grain": "One row per city",
        "columns": [
            ("GeographyKey", "Int64.Type", "Surrogate key.", "Relationship key.", True),
            ("Country", "type text", "Country (United States).", "Map context; top of geography hierarchy.", False),
            ("Region", "type text", "Sales region: Northeast, Midwest, South, West.", "Regional analysis; target grain.", False),
            ("State", "type text", "US state name.", "State analysis; filled map (data category: State or Province).", False),
            ("StateCode", "type text", "Two-letter state code.", "Compact labels.", False),
            ("City", "type text", "City name.", "City analysis (data category: City).", False),
            ("Latitude", "type number", "City latitude.", "Map placement (data category: Latitude).", True),
            ("Longitude", "type number", "City longitude.", "Map placement (data category: Longitude).", True),
        ],
    },
    "DimSalesChannel": {
        "description": "Sales channels.",
        "grain": "One row per channel",
        "columns": [
            ("ChannelKey", "Int64.Type", "Surrogate key.", "Relationship key.", True),
            ("ChannelCode", "type text", "Short code: ONL, RTL, MKT, B2B.", "Compact labels.", False),
            ("ChannelName", "type text", "Online Store, Retail Stores, Marketplace, B2B Wholesale.", "Channel slicer and analysis.", False),
            ("ChannelType", "type text", "Direct - Digital, Direct - Physical, Third-Party, Wholesale.", "Channel grouping.", False),
        ],
    },
    "FactSalesTarget": {
        "description": "Monthly net-sales targets from the finance plan.",
        "grain": "One row per Month x Region x Category x Channel",
        "columns": [
            ("TargetID", "Int64.Type", "Surrogate key.", "Unique row identifier.", True),
            ("TargetMonth", "type date", "First day of the target month.", "Relationship to DimDate[Date].", True),
            ("Region", "type text", "Sales region (matches DimGeography[Region]).", "Applied through TREATAS in the Sales Target measure.", True),
            ("Category", "type text", "Product category (matches DimProduct[Category]).", "Applied through TREATAS in the Sales Target measure.", True),
            ("ChannelKey", "Int64.Type", "Foreign key to DimSalesChannel.", "Relationship key.", True),
            ("TargetAmount", "Currency.Type", "Net-sales target in USD.", "Sales Target measure.", True),
        ],
    },
}


def columns(table: str) -> list[str]:
    return [c[0] for c in SCHEMA[table]["columns"]]
