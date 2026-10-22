# Business Insights

> **Illustrative findings from synthetic data.** Every number below was calculated from `data/processed/` (seed 42) by `scripts/calculate_kpis.py` or a documented pandas query; the full tables are in [kpi_reference.md](kpi_reference.md). Meridian Home & Office Co. is fictional. Some patterns (seasonality, regional drift, discount policy) were designed into the simulation; others (such as the West's 2024 spike) emerged from random customer behaviour. The purpose is to demonstrate how the dashboard turns data into decisions, not to make claims about a real market.

## Executive summary

Meridian generated **$9.15M net sales** and **$2.58M gross profit (28.2% margin)** over 2023-2025. After strong growth in 2024 (**+13.1%**), sales were **flat in 2025 (-0.3%)** and finished at **90.7% of target, $323.6K short**. Margin held steady (28.1-28.4%), so the 2025 problem is volume and mix, not pricing. The shortfall is concentrated in **B2B Wholesale** and the **Small Business** segment, while Online and Marketplace kept growing.

## 1. Overall performance (Executive Overview)

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| Net sales | $2.81M | $3.18M | $3.17M |
| YoY growth | n/a | +13.1% | -0.3% |
| Target achievement | 101.3% | 101.9% | 90.7% |
| Profit margin | 28.2% | 28.1% | 28.4% |
| Orders | 4,969 | 5,681 | 5,822 |
| Average order value | $565 | $559 | $544 |

- **What it means:** 2025 orders still grew (+2.5%) but average order value fell 2.7%, cancelling the gain.
- **Why AOV fell:** it is a **mix effect**. B2B Wholesale orders average about $1,160 versus about $360 in the other channels, and B2B orders fell from 1,410 to 1,303. Within B2B, AOV actually rose 1.7%.
- **Action:** treat 2025 as a B2B volume problem, not a pricing problem; review B2B account coverage before adjusting prices.

## 2. Channels

| Channel | Share of sales | 2024 growth | 2025 growth | 2025 target ach. |
|---|---|---|---|---|
| B2B Wholesale | 51.1% | +3.5% | **-6.0%** | 85.5% |
| Online Store | 28.2% | +38.0% | +6.3% | 97.0% |
| Retail Stores | 11.2% | +1.3% | -7.3% | 84.1% |
| Marketplace | 9.5% | +22.5% | +18.9% | 108.1% |

- B2B lost **$97K** and Retail **$26K** in 2025; Online (+$58K) and Marketplace (+$54K) offset most of it.
- **Action:** investigate B2B account churn and order frequency (Customer Detail drill-through); keep investing in Marketplace, the only channel above target in 2025. Watch Marketplace margin (25.8%, lowest of the channels).

## 3. Regions

| Region | Share | 2024 growth | 2025 growth | Target ach. 2023 / 2024 / 2025 |
|---|---|---|---|---|
| West | 30.5% | +30.5% | -6.9% | 111.8% / 117.7% / 84.8% |
| South | 28.2% | +15.1% | +6.8% | 111.0% / 103.5% / 97.4% |
| Northeast | 25.6% | +10.2% | -0.7% | 94.4% / 99.4% / 90.0% |
| Midwest | 15.7% | -12.5% | +1.6% | 86.6% / 78.8% / 92.4% |

- **South** is the most consistent performer: growth in both years and close to target in 2025.
- **West's** 2025 miss partly reflects its own 2024 surge: targets are prior-year actuals plus 10%, so an exceptional year sets a high bar. Treat it as a target-setting question as well as a performance one.
- **Midwest** missed target in all three years and is the only region smaller in 2025 than in 2023.
- Regional margins are nearly identical (27.9-28.6%), so regional differences are about volume, not profitability.
- **Action:** a recovery plan for the Midwest; review how targets are set after outlier years (e.g. a two-year average baseline).

## 4. Products and categories

- **Electronics is 48.2% of sales but earns only a 19.3% margin.** Laptops alone are **25.5% of sales at 10.5% margin**, and four of the top five products by revenue are laptops.
- The five lowest-margin products are all laptops (5.8%-14.3%), and their discount rates are low (3.2%-4.6%). Their weak margin is **structural** (list price vs cost), not caused by discounting.
- **Office Supplies** has the highest margin (43.2%) but fell **8.1%** in 2025 and reached only 83.6% of target - a profitable category losing volume, likely tied to the B2B decline (B2B buyers over-index on office supplies by design of the scenario).
- The top 10 products generate **43.2%** of sales, a moderate concentration.
- **Action:** renegotiate laptop costs or reprice; bundle accessories (40.8% margin) with laptops; protect Office Supplies volume with B2B replenishment programmes.

## 5. Customers

- **Concentration:** the top 20% of buyers generate **71.7%** of sales; A-tier customers (125 accounts, top 10%) generate **55.3%**. The single largest customer is 2.4% of sales - concentrated, but no single-account dependency.
- **Segments:** Corporate 46.1%, Small Business 31.9%, Consumer 21.9% of sales. Consumer sales grew in both years (+21.9%, +12.5%); **Small Business fell 10.3% in 2025**.
- **Breadth vs depth:** active customers rose from 971 to 1,075 in 2025, but sales per customer fell from $3,272 to $2,946.
- **Repeat behaviour:** 89.5% of buyers ordered at least twice over 2023-2025; within a single year about 76% do.
- **Action:** account plans for A-tier customers; a Small Business win-back campaign; onboarding offers that move one-time buyers (131 customers) to a second order.
- **Limitation:** no cost-to-serve or lifetime value data; "repeat" is order count, not loyalty.

## 6. Profitability and discounts

| Discount band | Share of sales | Profit margin |
|---|---|---|
| No discount | 51.6% | 31.0% |
| 1-10% | 25.9% | 27.9% |
| 11-20% | 20.7% | 23.6% |
| 21-30% | 1.1% | 12.6% |
| 31-40% | 0.7% | -2.4% |

- Discounted lines earn **25.2%** margin vs **31.0%** at full price. Discounts reduce overall margin by **5.2 percentage points** (list margin 33.4% vs realised 28.2%), costing **$711K** across three years.
- **228 order lines lost money** ($240K of sales, -$13.3K profit). Laptops (114 lines), Tables (52) and Desks (34) account for most of them.
- Tables (13.7% discount rate, 19.5% margin) and Desks (13.3%, 28.7%) are the most heavily discounted subcategories.
- **Correlation vs causation:** within a line, a deeper discount mechanically lowers margin - that is arithmetic. Across products, the correlation between discount rate and margin is weak (-0.11), because the lowest-margin products (laptops) are rarely discounted. The data cannot show whether discounts *generated* extra volume that paid for themselves; that would need a promotion calendar or a controlled test.
- **Action:** require approval for discounts above 20% (those bands earn 12.6% and -2.4%); A/B test smaller furniture promotions; track margin erosion monthly.

## 7. Seasonality and operations

- November and December deliver **20.9%, 21.0% and 21.4%** of annual sales in 2023-2025, and Q4 28.8%-30.3%. The pattern repeats in all three years, so it is reasonable to plan around it.
- Average order-to-ship time is **3.7 days** (Retail 0.5, Online 3.0, Marketplace 4.5, B2B 6.5). 70 orders were still open at the 31 Dec 2025 extract.
- **Action:** pre-build Q4 inventory and staffing; review B2B fulfilment lead times as part of the B2B retention plan.

## 8. Recommended management priorities

1. **Stabilise B2B Wholesale and Small Business** - account reviews, churn analysis, replenishment programmes (largest revenue gap).
2. **Fix laptop economics** - cost negotiation, repricing or accessory bundling (largest margin drag).
3. **Introduce discount guardrails** - approval above 20%, test-and-learn on furniture promotions.
4. **Midwest recovery plan** and a review of target-setting after outlier years.
5. **Keep scaling Marketplace and Online** while monitoring their margins.
