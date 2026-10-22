# Data

All files are **synthetic** and reproducible (`python scripts/generate_sales_data.py --seed 42`). They describe the fictional retailer Meridian Home & Office Co.

## raw/ - source extracts as delivered (contain deliberate data issues)

| File | Content |
|---|---|
| `orders_export_2023_2025.csv` | ERP order-line export: text-typed values, US dates, `$` amounts, `%` discounts, duplicates, test orders, name variants, some incorrect line totals |
| `product_master.csv` | 71 products with category, subcategory, brand, current list price and standard cost |
| `customer_master.csv` | 1,400 CRM accounts with segment, location and account-creation date |
| `geography_reference.csv` | 29 cities with state, region and coordinates |
| `sales_targets_2023_2025.xlsx` | Finance targets (sheet `Targets`) and a notes sheet (`ReadMe`) |

## processed/ - clean star schema loaded by Power BI

`FactSales.csv`, `FactSalesTarget.csv`, `DimDate.csv`, `DimProduct.csv`, `DimCustomer.csv`, `DimGeography.csv`, `DimSalesChannel.csv`

Format: UTF-8, comma-delimited, ISO dates, `true`/`false`, blank = null. Column definitions: [docs/data_dictionary.md](../docs/data_dictionary.md).

Also here: `cleaning_log.json` (every cleaning rule with rows affected) and `reference_kpis.json` (expected KPI values used to validate the report).

Rebuild with `python scripts/prepare_data.py` after regenerating the raw files. Cleaning rules: [docs/data_cleaning.md](../docs/data_cleaning.md).
