# Power BI Build Guide

This folder contains everything needed to build the report in **Power BI Desktop** (Windows). The `.pbip` project is **not yet included**: Power BI Desktop was not available in the environment where the data, model specification and measures were produced, so the report must be assembled following the steps below. Once built, save it here as a Power BI Project (`.pbip`) so the model and report are version-controlled as text.

| Asset | Purpose |
|---|---|
| `power_query/DataFolder.pq` | Text parameter pointing at `data/processed/` |
| `power_query/<Table>.pq` | One typed load query per table (7 tables) |
| `tmdl/measures.tmdl` | Script that creates all 78 measures with formats and display folders |
| `dax_measures.md` | Readable documentation of every measure |
| `theme/meridian_executive_theme.json` | Report theme (colours, fonts, visual defaults) |
| `../docs/dashboard_design.md` | Page-by-page layout with pixel positions |
| `../docs/kpi_reference.md` | Expected values to validate the finished report |

Estimated build time: 3-5 hours for an experienced Power BI developer.

## Step 0 - Prerequisites

- Power BI Desktop (current version, which includes TMDL view). Enable *File > Options > Preview features > Power BI Project (.pbip) save option* if your version still lists it as a preview.
- Run the Python pipeline once, or use the committed CSVs in `data/processed/`.

## Step 1 - Load the data (Power Query)

1. **File > Options > Current file > Data load**: uncheck **Auto date/time**.
2. **Home > Transform data > Manage Parameters > New**: name `DataFolder`, type **Text**, current value = full path to `data\processed\` **including the trailing backslash**.
3. For each table in this order - `DimDate`, `DimProduct`, `DimCustomer`, `DimGeography`, `DimSalesChannel`, `FactSales`, `FactSalesTarget`:
   **Home > New source > Blank query** > **Advanced Editor** > paste the contents of `power_query/<Table>.pq` > rename the query to the table name.
4. **Close & Apply.** Check row counts in Table view against [`docs/validation_report.md`](../docs/validation_report.md) (FactSales 31,952; FactSalesTarget 2,304; DimDate 1,096; DimProduct 71; DimCustomer 1,400; DimGeography 29; DimSalesChannel 4).

## Step 2 - Build the model

1. **Model view**: delete any auto-detected relationships, then create the eight relationships listed in [`docs/data_model.md`](../docs/data_model.md#2-relationships-to-create-in-power-bi-desktop). Make `FactSales[ShipDate] -> DimDate[Date]` **inactive**. All cross-filter directions **Single**.
2. Select `DimDate` > **Table tools > Mark as date table** > `Date`.
3. Apply **Sort by column** for every pair listed in the data model doc (e.g. `MonthName` by `MonthNumber`, `YearMonth` by `YearMonthNumber`).
4. Create hierarchies: *Calendar* (Year > Quarter > MonthName > Date), *Product* (Category > Subcategory > ProductName), *Geography* (Region > State > City).
5. Set data categories on DimGeography (State, City, Country, Latitude, Longitude).
6. Hide every column marked **Hidden** in [`docs/data_dictionary.md`](../docs/data_dictionary.md).

## Step 3 - Add the measures

1. **Home > Enter data**: create a one-column table named `_Measures` (leave it empty or with one blank row) and load it.
2. **TMDL view** > **+ (new script tab)** > paste the full contents of `tmdl/measures.tmdl` > **Apply**.
3. Confirm 78 measures appear under `_Measures` in seven display folders, then hide the placeholder column. Power BI now shows `_Measures` with a calculator icon at the top of the field list.
4. If TMDL view reports a syntax problem (TMDL is whitespace-sensitive; the script uses tabs), create measures manually from [`dax_measures.md`](dax_measures.md) with **Modeling > New measure**, or paste them through Tabular Editor.

> The DAX was written and statically checked (every table, column and measure reference is linted by `tests/data_quality_checks.py`), but it has **not been executed** in Power BI. Step 6 is how you verify it.

## Step 4 - Apply the theme

**View > Themes > Browse for themes** > `theme/meridian_executive_theme.json`.

## Step 5 - Build the pages

Follow [`docs/dashboard_design.md`](../docs/dashboard_design.md):

1. Create pages: `Executive Overview`, `Sales Trends`, `Products`, `Regions`, `Customers`, `Profitability`, `Product Detail`, `Customer Detail`, `Tooltip - Margin`.
2. Build the shared header, filter strip and KPI row on the Executive page; **copy-paste** them to the other pages (Power BI asks to sync slicers - choose *Sync*).
3. Add page-specific visuals using the positions and fields in the spec.
4. Configure drill-through on the two detail pages, set the tooltip page size to 320 x 240 and *Allow use as tooltip*.
5. Add the **page navigator** button group to the header and **Back** buttons on drill-through pages.
6. Create a bookmark **Default view** with all slicers cleared (Data option on) and link it to the Reset button.
7. Set alt text and tab order.
8. Hide `Product Detail`, `Customer Detail` and `Tooltip - Margin` from the page tabs.

## Step 6 - Validate

Work through the manual checklist in [`docs/testing_and_validation.md`](../docs/testing_and_validation.md#3-manual-checks-in-power-bi-desktop). At minimum, confirm in a matrix with no filters that **Total Sales = $9,153,711**, **Total Profit = $2,584,676**, **Profit Margin % = 28.2%**, **Total Orders = 16,472**, and that 2025 **Target Achievement % = 90.7%**.

## Step 7 - Save as a project and commit

**File > Save as** > type **Power BI project (*.pbip)** > save as `powerbi/Sales_Performance_Dashboard.pbip`. Commit the resulting `Sales_Performance_Dashboard.SemanticModel/` and `Sales_Performance_Dashboard.Report/` folders (the `.gitignore` already excludes local cache and settings files).

Then take screenshots of each page (1280 x 720 or larger) into `docs/screenshots/` using the file names listed in `docs/screenshots/README.md`, and replace the placeholders in the main README.

## Optional - Publish

If you have a Power BI Pro licence, publish to the Power BI service and use **File > Embed report > Publish to web** only for this synthetic dataset (never for client data). Add the public link to your portfolio once it exists.
