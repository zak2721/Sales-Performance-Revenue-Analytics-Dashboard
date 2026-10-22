# Portfolio Case Study: Sales Performance & Business Intelligence Dashboard

*Power BI | DAX | Power Query | Data Modeling | Sales Analytics*

> Portfolio project built on synthetic data for a fictional retailer. It demonstrates an end-to-end BI delivery process; it is not a client engagement.

## The (hypothetical) client problem

Meridian Home & Office Co., a multi-channel retailer selling across four US regions, reported performance from hand-built monthly spreadsheets. Numbers changed between versions because duplicate and test orders were cleaned inconsistently, leaders could see *that* sales moved but not *why*, and finance targets were compared with actuals only at quarter end.

## The solution

An end-to-end Power BI solution, delivered the way a consultant would hand it over:

1. **Data preparation pipeline** - a reproducible Python process that cleans an ERP order export (duplicates, test accounts, inconsistent region/category/channel names, line totals that ignored discounts) and logs every rule with row counts.
2. **Star-schema model** - one sales fact at order-line grain, a monthly target fact, and five conformed dimensions; single-direction relationships, a marked date table, an inactive ship-date relationship, and a TREATAS pattern that connects coarse-grained targets without many-to-many relationships.
3. **78 documented DAX measures** - sales, profitability, time intelligence (MoM, YoY, YTD, rolling), target attainment with grain protection, contribution and Top N, customer behaviour, and dynamic titles - delivered as both documentation and a deployable TMDL script.
4. **Six-page report design** - Executive Overview, Sales Trends, Product Performance, Regional Performance, Customer Insights, Profitability & Discounts - plus drill-through and tooltip pages, a custom theme and pixel-level layout spec.
5. **Validation** - 17 automated data-quality checks and an independently calculated set of expected KPI values used to verify the Power BI measures.
6. **Insight narrative** - findings and recommended actions for management.

## Business questions answered

- How much revenue and profit are we generating, and is it growing?
- Are we on target - overall, by region, category and channel?
- Which products and categories drive sales, and which sell well but earn weak margins?
- Which regions and channels are under-performing, and since when?
- How concentrated is revenue among customers, and how often do they return?
- How much margin do discounts cost, and where are we losing money?

## Example findings (illustrative, synthetic data)

- Sales grew 13.1% in 2024 then flattened (-0.3%) in 2025, closing at 90.7% of target. The model traced the gap to a 6.0% decline in B2B Wholesale; Online and Marketplace kept growing.
- Lower average order value in 2025 was a channel-mix effect, not price erosion: B2B AOV actually rose.
- Laptops were 25.5% of sales at a 10.5% margin - a structural pricing/cost issue, since they are rarely discounted.
- Discounts reduced margin by 5.2 percentage points; lines discounted more than 30% lost money.
- The top 20% of customers generated 71.7% of sales.

## Technical skills demonstrated

| Skill | Evidence |
|---|---|
| Power BI data modelling | Star schema, relationship design, date table, inactive relationships, TREATAS for mixed-grain facts |
| DAX | 78 measures: time intelligence, ranking/Top N, ALLSELECTED contribution, filter-context guards, dynamic titles, conditional-formatting measures |
| Power Query (M) | Parameterised, typed loads with culture-safe parsing and null handling |
| Data cleaning | Documented, logged and tested cleaning rules |
| Data quality & testing | Automated checks; reference KPI values for report validation |
| Dashboard design | Theme, grid, colour semantics, accessibility, interaction design |
| Business analysis | KPI framework, driver analysis, correlation-vs-causation discipline, recommendations |
| Engineering practice | Git, reproducible pipeline (fixed seed), single source of truth for schema and measures |

## Potential value for a business

- One trusted set of numbers, refreshed in minutes instead of rebuilt monthly by hand.
- Target gaps visible monthly by region, category and channel, not at quarter end.
- A clear split between volume problems, pricing/cost problems and discount problems, so each goes to the right owner.
- A foundation that can be pointed at live sources (SQL, SharePoint, ERP) without redesigning the model.
