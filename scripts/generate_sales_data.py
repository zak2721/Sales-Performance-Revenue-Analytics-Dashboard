"""
Generate the SYNTHETIC source data for the Sales Performance & BI Dashboard project.

Everything produced here is fictional. "Meridian Home & Office Co." is an invented
retailer; customers, products and cities-as-customer-locations are simulated.

Outputs (data/raw/ by default) mimic what a BI consultant typically receives:
  * orders_export_2023_2025.csv      - flat ERP order-line export (with realistic data issues)
  * product_master.csv               - product master from the merchandising system
  * customer_master.csv              - customer master from the CRM
  * geography_reference.csv          - city reference list with coordinates
  * sales_targets_2023_2025.xlsx     - finance plan (monthly targets)

Design of the simulation (documented in docs/data_cleaning.md):
  * 2022 is simulated but NOT exported; it is only used to build the 2023 targets
    the same way finance would (prior-year actuals x planned growth).
  * Demand has a fixed monthly seasonality (Nov/Dec peak), weekday effects,
    company growth, regional growth differences and a shifting channel mix.
  * Discounts depend on channel, subcategory and the Nov/Dec promotion window.
  * Injected data issues: exact duplicate rows, inconsistent text casing/spacing,
    channel-name variants, a test account, line totals that ignore the discount,
    open (unshipped) orders with a blank ship date.

Usage:
    python scripts/generate_sales_data.py [--seed 42] [--output-dir data/raw]
"""
from __future__ import annotations

import argparse
import math
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_SEED = 42
SIM_START = date(2022, 1, 1)      # 2022 simulated for target baselines only
EXPORT_START = date(2023, 1, 1)
EXTRACT_DATE = date(2025, 12, 31)  # data extract date: later ship dates are not yet known

COMPANY = "Meridian Home & Office Co. (fictional)"

# --------------------------------------------------------------------------------------
# Reference data
# --------------------------------------------------------------------------------------
# (City, State, StateCode, Region, Latitude, Longitude, relative market weight)
CITIES = [
    ("New York", "New York", "NY", "Northeast", 40.7128, -74.0060, 3.0),
    ("Buffalo", "New York", "NY", "Northeast", 42.8864, -78.8784, 0.6),
    ("Boston", "Massachusetts", "MA", "Northeast", 42.3601, -71.0589, 1.4),
    ("Philadelphia", "Pennsylvania", "PA", "Northeast", 39.9526, -75.1652, 1.4),
    ("Pittsburgh", "Pennsylvania", "PA", "Northeast", 40.4406, -79.9959, 0.7),
    ("Newark", "New Jersey", "NJ", "Northeast", 40.7357, -74.1724, 0.8),
    ("Hartford", "Connecticut", "CT", "Northeast", 41.7658, -72.6734, 0.5),
    ("Chicago", "Illinois", "IL", "Midwest", 41.8781, -87.6298, 2.2),
    ("Detroit", "Michigan", "MI", "Midwest", 42.3314, -83.0458, 0.9),
    ("Columbus", "Ohio", "OH", "Midwest", 39.9612, -82.9988, 0.9),
    ("Cleveland", "Ohio", "OH", "Midwest", 41.4993, -81.6944, 0.7),
    ("Minneapolis", "Minnesota", "MN", "Midwest", 44.9778, -93.2650, 0.9),
    ("Indianapolis", "Indiana", "IN", "Midwest", 39.7684, -86.1581, 0.8),
    ("Milwaukee", "Wisconsin", "WI", "Midwest", 43.0389, -87.9065, 0.6),
    ("Houston", "Texas", "TX", "South", 29.7604, -95.3698, 1.8),
    ("Dallas", "Texas", "TX", "South", 32.7767, -96.7970, 1.6),
    ("Austin", "Texas", "TX", "South", 30.2672, -97.7431, 1.0),
    ("Atlanta", "Georgia", "GA", "South", 33.7490, -84.3880, 1.4),
    ("Miami", "Florida", "FL", "South", 25.7617, -80.1918, 1.3),
    ("Orlando", "Florida", "FL", "South", 28.5383, -81.3792, 0.8),
    ("Charlotte", "North Carolina", "NC", "South", 35.2271, -80.8431, 0.9),
    ("Nashville", "Tennessee", "TN", "South", 36.1627, -86.7816, 0.8),
    ("Los Angeles", "California", "CA", "West", 34.0522, -118.2437, 2.6),
    ("San Francisco", "California", "CA", "West", 37.7749, -122.4194, 1.3),
    ("San Diego", "California", "CA", "West", 32.7157, -117.1611, 1.0),
    ("Seattle", "Washington", "WA", "West", 47.6062, -122.3321, 1.2),
    ("Portland", "Oregon", "OR", "West", 45.5152, -122.6784, 0.7),
    ("Denver", "Colorado", "CO", "West", 39.7392, -104.9903, 0.9),
    ("Phoenix", "Arizona", "AZ", "West", 33.4484, -112.0740, 1.1),
]

# Annual demand multiplier by region (compounded from 2022). Midwest is deliberately soft.
REGION_TREND = {"Northeast": 1.06, "Midwest": 0.96, "South": 1.15, "West": 1.09}

CHANNELS = {
    # code: (name, base share 2022, annual trend, ship-days range, any-discount prob)
    "ONL": ("Online Store", 0.30, 1.16, (1, 5), 0.30),
    "RTL": ("Retail Stores", 0.40, 0.95, (0, 1), 0.22),
    "MKT": ("Marketplace", 0.17, 1.12, (2, 7), 0.42),
    "B2B": ("B2B Wholesale", 0.13, 1.03, (3, 10), 0.60),
}

SEGMENT_CHANNEL_PREF = {
    "Consumer":       {"ONL": 0.40, "RTL": 0.42, "MKT": 0.18, "B2B": 0.00},
    "Small Business": {"ONL": 0.35, "RTL": 0.20, "MKT": 0.15, "B2B": 0.30},
    "Corporate":      {"ONL": 0.20, "RTL": 0.05, "MKT": 0.05, "B2B": 0.70},
}
SEGMENT_SHARE = {"Consumer": 0.60, "Small Business": 0.28, "Corporate": 0.12}
SEGMENT_WEIGHT = {"Consumer": 1.0, "Small Business": 2.0, "Corporate": 4.0}

CHANNEL_CATEGORY_AFFINITY = {
    "ONL": {"Electronics": 1.3, "Furniture": 0.8, "Office Supplies": 1.0, "Home & Kitchen": 1.1},
    "RTL": {"Electronics": 1.0, "Furniture": 1.2, "Office Supplies": 0.9, "Home & Kitchen": 1.2},
    "MKT": {"Electronics": 1.2, "Furniture": 0.7, "Office Supplies": 1.0, "Home & Kitchen": 1.3},
    "B2B": {"Electronics": 0.9, "Furniture": 1.3, "Office Supplies": 2.0, "Home & Kitchen": 0.3},
}

MONTH_SEASONALITY = {1: 0.80, 2: 0.80, 3: 0.95, 4: 0.95, 5: 1.00, 6: 0.95,
                     7: 0.95, 8: 1.08, 9: 1.00, 10: 1.05, 11: 1.30, 12: 1.40}
WEEKDAY_FACTOR = {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 5: 0.85, 6: 0.70}
YEAR_FACTOR = {2022: 1.00, 2023: 1.10, 2024: 1.21, 2025: 1.29}  # company-level order growth
BASE_ORDERS_PER_DAY = 13.0
PRICE_INFLATION = 1.03  # list prices and costs rise 3% per year from the 2022 base

# Finance plan: planned growth on prior-year actuals used to set each year's targets
PLANNED_GROWTH = {2023: 0.12, 2024: 0.11, 2025: 0.10}

# Subcategory definitions:
# category, subcategory, code, (price low, high), list margin, popularity, discount propensity,
# deep-discount eligible, consumable (bulk quantities)
SUBCATEGORIES = [
    ("Electronics", "Laptops", "LAP", (749, 1599), 0.14, 0.60, 0.7, False, False),
    ("Electronics", "Monitors", "MON", (179, 449), 0.22, 0.80, 1.0, False, False),
    ("Electronics", "Audio", "AUD", (39, 299), 0.35, 1.00, 1.0, False, False),
    ("Electronics", "Accessories", "ACC", (15, 89), 0.45, 1.60, 1.0, False, True),
    ("Furniture", "Office Chairs", "CHR", (149, 599), 0.42, 0.90, 1.3, True, False),
    ("Furniture", "Desks", "DSK", (249, 899), 0.38, 0.50, 1.6, True, False),
    ("Furniture", "Storage", "STO", (79, 349), 0.40, 0.70, 1.0, False, False),
    ("Furniture", "Tables", "TBL", (199, 699), 0.30, 0.45, 1.8, True, False),
    ("Office Supplies", "Paper & Notebooks", "PAP", (5, 29), 0.50, 2.00, 1.0, False, True),
    ("Office Supplies", "Writing Instruments", "WRT", (3, 25), 0.55, 2.00, 1.0, False, True),
    ("Office Supplies", "Organization", "ORG", (9, 59), 0.48, 1.20, 1.0, False, True),
    ("Office Supplies", "Printing Supplies", "PRT", (19, 119), 0.40, 1.20, 1.0, False, True),
    ("Home & Kitchen", "Small Appliances", "APL", (39, 249), 0.33, 0.90, 1.0, False, False),
    ("Home & Kitchen", "Cookware", "CKW", (25, 179), 0.42, 1.00, 1.0, False, False),
    ("Home & Kitchen", "Lighting", "LGT", (19, 149), 0.45, 0.90, 1.0, False, False),
    ("Home & Kitchen", "Home Decor", "DEC", (15, 119), 0.52, 1.00, 1.0, False, False),
]

PRODUCT_NAMES = {
    "LAP": ["Aurora 14 Ultrabook", "Vertex 15 Pro Laptop", "Nimbus 13 Air Laptop", "Orion 16 Workstation Laptop", "Summit 14 Business Laptop"],
    "MON": ["Lumen 24in FHD Monitor", "Lumen 27in QHD Monitor", "Vertex 32in 4K Monitor", "Orion 34in Ultrawide Monitor"],
    "AUD": ["Halcyon Wireless Earbuds", "Halcyon Over-Ear Headphones", "Cedar Bluetooth Speaker", "Atlas Conference Speakerphone", "Nimbus USB Headset"],
    "ACC": ["Keystone Wireless Mouse", "Keystone Mechanical Keyboard", "Atlas USB-C Hub", "Cedar Laptop Sleeve 15in", "Atlas 65W USB-C Charger"],
    "CHR": ["Summit Ergonomic Task Chair", "Summit Mesh Executive Chair", "Cedar Guest Chair", "Atlas Drafting Stool"],
    "DSK": ["Keystone Sit-Stand Desk", "Cedar Writing Desk", "Summit L-Shaped Desk", "Atlas Compact Desk"],
    "STO": ["Keystone 2-Drawer File Cabinet", "Cedar 5-Shelf Bookcase", "Atlas Mobile Pedestal", "Keystone Storage Cabinet"],
    "TBL": ["Summit Conference Table 8ft", "Cedar Round Meeting Table", "Atlas Folding Training Table", "Cedar Coffee Table"],
    "PAP": ["Meridian Copy Paper (Ream)", "Meridian Spiral Notebook 3-Pack", "Meridian Sticky Notes 12-Pack", "Meridian Legal Pads 6-Pack", "Meridian Hardcover Journal"],
    "WRT": ["Meridian Gel Pens 12-Pack", "Meridian Ballpoint Pens 24-Pack", "Meridian Highlighters 8-Pack", "Meridian Whiteboard Markers 6-Pack", "Meridian Mechanical Pencils 10-Pack"],
    "ORG": ["Keystone Desk Organizer", "Keystone Hanging File Folders 25-Pack", "Keystone Label Maker", "Keystone Binder Set"],
    "PRT": ["Vertex Black Toner Cartridge", "Vertex Color Ink Combo", "Vertex Photo Paper 50-Pack", "Vertex Laser Toner High-Yield"],
    "APL": ["Cedar Drip Coffee Maker", "Cedar Electric Kettle", "Lumen Air Fryer", "Halcyon Countertop Blender"],
    "CKW": ["Cedar Nonstick Fry Pan Set", "Cedar Stainless Cookware 10-Piece", "Atlas Cast Iron Skillet", "Cedar Chef Knife Set", "Atlas Bakeware Set"],
    "LGT": ["Lumen LED Desk Lamp", "Lumen Floor Lamp", "Lumen Smart Bulb 4-Pack", "Lumen Pendant Light"],
    "DEC": ["Halcyon Wall Clock", "Halcyon Throw Pillow Set", "Halcyon Framed Wall Art", "Halcyon Ceramic Vase", "Halcyon Area Rug 5x7"],
}

FIRST_NAMES = ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda", "David", "Elizabeth",
               "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Carlos", "Karen",
               "Daniel", "Lisa", "Matthew", "Nancy", "Anthony", "Sandra", "Mark", "Ashley", "Steven", "Emily",
               "Andrew", "Michelle", "Joshua", "Amanda", "Kevin", "Melissa", "Brian", "Aisha", "Wei", "Priya",
               "Luis", "Grace", "Omar", "Hannah", "Diego", "Mei", "Samuel", "Fatima", "Noah", "Olivia"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
              "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
              "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
              "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
              "Patel", "Kim", "Chen", "Okafor", "Haile", "Novak", "Rossi", "Silva", "Cohen", "Murphy"]
BIZ_WORDS_A = ["Blue", "Granite", "Harbor", "Pine", "Silver", "North", "Bright", "Oak", "River", "Summit",
               "Copper", "Maple", "Iron", "Crescent", "Lakeside", "Prairie", "Redwood", "Beacon", "Cobalt", "Sterling"]
BIZ_WORDS_B = ["Ridge", "Point", "Field", "Gate", "Stone", "Bridge", "Peak", "Valley", "Works", "Path"]
BIZ_TYPES = ["Consulting", "Logistics", "Dental Group", "Architects", "Law Partners", "Marketing", "Realty",
             "Engineering", "Health Clinic", "Accounting", "Design Studio", "Academy", "Builders", "Software"]
BIZ_SUFFIX = ["LLC", "Inc.", "Co.", "Group", "Partners"]


# --------------------------------------------------------------------------------------
# Builders
# --------------------------------------------------------------------------------------
def build_products(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for cat, sub, code, (lo, hi), margin, pop, disc_prop, deep, consumable in SUBCATEGORIES:
        names = PRODUCT_NAMES[code]
        prices = np.sort(rng.uniform(lo, hi, size=len(names)))
        for i, name in enumerate(names, start=1):
            base_price = math.floor(prices[i - 1]) + 0.99  # 2022 list price
            prod_margin = float(np.clip(margin + rng.normal(0, 0.03), 0.08, 0.70))
            rows.append({
                "ProductID": f"{cat[:3].upper()}-{code}-{i:03d}",
                "ProductName": name,
                "Category": cat,
                "Subcategory": sub,
                "Brand": name.split()[0],
                "BaseListPrice2022": round(base_price, 2),
                "ListMargin": round(prod_margin, 4),
                "Popularity": float(pop * rng.lognormal(0, 0.45)),
                "DiscountPropensity": disc_prop,
                "DeepDiscountEligible": deep,
                "Consumable": consumable,
            })
    return pd.DataFrame(rows)


def year_price(base_price: float, year: int) -> float:
    """List price in a given year: 3% annual increase, kept on a .99 price point."""
    p = base_price * PRICE_INFLATION ** (year - 2022)
    return round(math.floor(p) + 0.99, 2)


def year_cost(price: float, margin: float) -> float:
    return round(price * (1 - margin), 2)


def build_customers(rng: np.random.Generator, n: int = 1400) -> pd.DataFrame:
    cities = pd.DataFrame(CITIES, columns=["City", "State", "StateCode", "Region", "Lat", "Lon", "Weight"])
    city_idx = rng.choice(len(cities), size=n, p=cities["Weight"] / cities["Weight"].sum())
    segments = rng.choice(list(SEGMENT_SHARE), size=n, p=list(SEGMENT_SHARE.values()))
    sim_days = (EXTRACT_DATE - SIM_START).days
    # 45% of customers already active at the start of 2022; the rest are acquired over time
    acquired_offset = np.where(rng.random(n) < 0.45, 0, rng.integers(0, sim_days - 30, size=n))
    used_names: set[str] = set()
    rows = []
    for i in range(n):
        seg = segments[i]
        while True:
            if seg == "Consumer":
                name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
            else:
                name = (f"{rng.choice(BIZ_WORDS_A)}{rng.choice(BIZ_WORDS_B).lower()} "
                        f"{rng.choice(BIZ_TYPES)} {rng.choice(BIZ_SUFFIX)}")
            if name not in used_names:
                used_names.add(name)
                break
        c = cities.iloc[city_idx[i]]
        since = SIM_START + timedelta(days=int(acquired_offset[i]))
        if acquired_offset[i] == 0:  # long-standing account: signup date before 2022
            since = SIM_START - timedelta(days=int(rng.integers(30, 1500)))
        rows.append({
            "CustomerID": f"C-{10001 + i}",
            "CustomerName": name,
            "Segment": seg,
            "City": c["City"],
            "State": c["State"],
            "Region": c["Region"],
            "CustomerSince": since,
            "ActiveFrom": max(since, SIM_START),
            "Weight": float(rng.lognormal(0, 1.0) * SEGMENT_WEIGHT[seg]),
        })
    return pd.DataFrame(rows)


def simulate_orders(rng: np.random.Generator, products: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    """Simulate order lines from 2022-01-01 to the extract date."""
    cust_weight = customers["Weight"].to_numpy()
    cust_region = customers["Region"].to_numpy()
    cust_active = pd.to_datetime(customers["ActiveFrom"]).dt.date.to_numpy()
    cust_segment = customers["Segment"].to_numpy()
    region_trend = np.array([REGION_TREND[r] for r in cust_region])

    prod_cat = products["Category"].to_numpy()
    prod_pop = products["Popularity"].to_numpy()
    channel_codes = list(CHANNELS)

    lines = []
    order_seq = {}
    d = SIM_START
    while d <= EXTRACT_DATE:
        y = d.year
        years_since = (d - SIM_START).days / 365.25
        lam = BASE_ORDERS_PER_DAY * YEAR_FACTOR[y] * MONTH_SEASONALITY[d.month] * WEEKDAY_FACTOR[d.weekday()]
        n_orders = rng.poisson(lam)
        if n_orders:
            active = cust_active <= d
            p = cust_weight * active * region_trend ** years_since
            p = p / p.sum()
            chosen = rng.choice(len(customers), size=n_orders, p=p)
            for ci in chosen:
                seg = cust_segment[ci]
                ch_p = np.array([SEGMENT_CHANNEL_PREF[seg][c] * CHANNELS[c][2] ** years_since
                                 * (0.1 if (c == "B2B" and d.weekday() >= 5) else 1.0)
                                 for c in channel_codes])
                ch = channel_codes[rng.choice(4, p=ch_p / ch_p.sum())]
                order_seq[y] = order_seq.get(y, 0) + 1
                order_id = f"SO-{y}-{order_seq[y]:06d}"
                lo, hi = CHANNELS[ch][3]
                ship = d + timedelta(days=int(rng.integers(lo, hi + 1)))
                n_lines = int(min(1 + rng.poisson(0.8 if ch != "B2B" else 1.4), 6))
                aff = np.array([CHANNEL_CATEGORY_AFFINITY[ch][c] for c in prod_cat])
                pp = prod_pop * aff
                prod_idx = rng.choice(len(products), size=n_lines, replace=False, p=pp / pp.sum())
                promo = d.month in (11, 12)
                for ln, pi in enumerate(prod_idx, start=1):
                    prod = products.iloc[pi]
                    # quantity
                    if prod["Consumable"]:
                        qty = 4 + rng.poisson(6) if ch == "B2B" else 1 + rng.poisson(1.2)
                    elif prod["Subcategory"] == "Laptops":
                        qty = 1 + rng.poisson(1.2) if ch == "B2B" else 1
                    else:
                        qty = 1 + rng.poisson(2.0) if ch == "B2B" else 1 + int(rng.random() < 0.15)
                    # discount
                    p_disc = min(CHANNELS[ch][4] * prod["DiscountPropensity"] + (0.15 if promo else 0), 0.95)
                    disc = 0.0
                    if rng.random() < p_disc:
                        if prod["DeepDiscountEligible"] and (ch in ("MKT", "RTL") or promo):
                            disc = float(rng.choice([0.10, 0.20, 0.30, 0.40], p=[0.25, 0.30, 0.25, 0.20]))
                        elif ch == "B2B":
                            disc = float(rng.choice([0.10, 0.15, 0.20], p=[0.45, 0.35, 0.20]))
                        else:
                            disc = float(rng.choice([0.05, 0.10, 0.15, 0.20], p=[0.35, 0.35, 0.20, 0.10]))
                    price = year_price(prod["BaseListPrice2022"], y)
                    cost = year_cost(price, prod["ListMargin"])
                    lines.append((order_id, ln, d, ship, customers.at[ci, "CustomerID"], ch,
                                  prod["ProductID"], int(qty), price, cost, disc))
        d += timedelta(days=1)

    df = pd.DataFrame(lines, columns=["OrderID", "OrderLine", "OrderDate", "ShipDate", "CustomerID", "Channel",
                                      "ProductID", "Quantity", "UnitPrice", "UnitCost", "DiscountPct"])
    gross = (df["Quantity"] * df["UnitPrice"]).round(2)
    disc_amt = (gross * df["DiscountPct"]).round(2)
    df["NetSales"] = (gross - disc_amt).round(2)
    return df


def build_targets(rng: np.random.Generator, lines: pd.DataFrame, products: pd.DataFrame,
                  customers: pd.DataFrame) -> pd.DataFrame:
    """Finance plan: prior-year actuals by Region x Category x Channel x planned growth,
    phased across months with the company's prior-year monthly sales profile."""
    df = lines.merge(products[["ProductID", "Category"]], on="ProductID") \
              .merge(customers[["CustomerID", "Region"]], on="CustomerID")
    df["Year"] = pd.to_datetime(df["OrderDate"]).dt.year
    df["Month"] = pd.to_datetime(df["OrderDate"]).dt.month
    rows = []
    for year, growth in PLANNED_GROWTH.items():
        prior = df[df["Year"] == year - 1]
        annual = prior.groupby(["Region", "Category", "Channel"])["NetSales"].sum()
        phasing = prior.groupby("Month")["NetSales"].sum()
        phasing = phasing / phasing.sum()
        for (region, cat, ch), amount in annual.items():
            for m in range(1, 13):
                target = amount * (1 + growth) * phasing[m] * rng.normal(1.0, 0.02)
                rows.append({"Fiscal Year": year, "Month": date(year, m, 1).strftime("%b"),
                             "Region": region, "Category": cat, "Channel": CHANNELS[ch][0],
                             "Target (USD)": round(float(target), -1)})
    out = pd.DataFrame(rows)
    # complete the grid (a combination with no prior-year sales gets a zero target)
    return out


# --------------------------------------------------------------------------------------
# Raw export with realistic data-quality issues
# --------------------------------------------------------------------------------------
def money(x: float) -> str:
    return f"${x:,.2f}"


def build_raw_export(rng: np.random.Generator, lines: pd.DataFrame, products: pd.DataFrame,
                     customers: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df = lines[pd.to_datetime(lines["OrderDate"]).dt.date >= EXPORT_START].copy()
    df = df.merge(products[["ProductID", "ProductName", "Category", "Subcategory"]], on="ProductID") \
           .merge(customers[["CustomerID", "CustomerName", "Segment", "City", "State", "Region"]], on="CustomerID")
    df = df.sort_values(["OrderDate", "OrderID", "OrderLine"]).reset_index(drop=True)

    open_mask = df["ShipDate"] > EXTRACT_DATE
    raw = pd.DataFrame({
        "Order ID": df["OrderID"],
        "Order Line": df["OrderLine"],
        "Order Date": pd.to_datetime(df["OrderDate"]).dt.strftime("%m/%d/%Y"),
        "Ship Date": np.where(open_mask, "", pd.to_datetime(df["ShipDate"]).dt.strftime("%m/%d/%Y")),
        "Order Status": np.where(open_mask, "Open", "Shipped"),
        "Customer ID": df["CustomerID"],
        "Customer Name": df["CustomerName"],
        "Customer Segment": df["Segment"],
        "City": df["City"],
        "State": df["State"],
        "Region": df["Region"],
        "Sales Channel": df["Channel"].map(lambda c: CHANNELS[c][0]),
        "Product ID": df["ProductID"],
        "Product Name": df["ProductName"],
        "Category": df["Category"],
        "Sub-Category": df["Subcategory"],
        "Quantity": df["Quantity"].astype(str),
        "Unit Price": df["UnitPrice"].map(money),
        "Unit Cost": df["UnitCost"].map(money),
        "Discount": (df["DiscountPct"] * 100).round(0).astype(int).astype(str) + "%",
        "Line Total": df["NetSales"].map(money),
    })
    n = len(raw)
    issues = {}

    # 1) inconsistent casing / whitespace in category and region text
    idx = rng.choice(n, size=int(n * 0.02), replace=False)
    raw.loc[idx, "Category"] = raw.loc[idx, "Category"].map(lambda s: rng.choice([s.lower(), s.upper(), f" {s} "]))
    idx = rng.choice(n, size=int(n * 0.01), replace=False)
    raw.loc[idx, "Region"] = raw.loc[idx, "Region"].map(lambda s: f"{s.upper()} ")
    issues["category_text_variants"] = int(n * 0.02)
    issues["region_text_variants"] = int(n * 0.01)

    # 2) channel naming variants from a legacy POS feed
    variants = {"Online Store": ["Online", "online store", "Web Store"], "Retail Stores": ["Retail", "Store"],
                "Marketplace": ["Market Place", "3P Marketplace"], "B2B Wholesale": ["Wholesale", "B2B"]}
    idx = rng.choice(n, size=int(n * 0.03), replace=False)
    raw.loc[idx, "Sales Channel"] = raw.loc[idx, "Sales Channel"].map(lambda s: rng.choice(variants[s]))
    issues["channel_name_variants"] = int(n * 0.03)

    # 3) line totals exported before discount (system bug on a subset of discounted lines)
    disc_rows = raw.index[raw["Discount"] != "0%"].to_numpy()
    idx = rng.choice(disc_rows, size=40, replace=False)
    gross = df.loc[idx, "Quantity"] * df.loc[idx, "UnitPrice"]
    raw.loc[idx, "Line Total"] = gross.round(2).map(money)
    issues["line_total_ignores_discount"] = 40

    # 4) internal test account orders
    test_rows = []
    for k in range(3):
        d = date(2024, 3, 4 + k)
        for ln in (1, 2):
            p = products.iloc[int(rng.integers(len(products)))]
            price = year_price(p["BaseListPrice2022"], 2024)
            test_rows.append({
                "Order ID": f"SO-TEST-{k + 1:03d}", "Order Line": ln, "Order Date": d.strftime("%m/%d/%Y"),
                "Ship Date": d.strftime("%m/%d/%Y"), "Order Status": "Shipped", "Customer ID": "C-TEST-01",
                "Customer Name": "TEST ACCOUNT - DO NOT USE", "Customer Segment": "Consumer", "City": "Chicago",
                "State": "Illinois", "Region": "Midwest", "Sales Channel": "Online Store",
                "Product ID": p["ProductID"], "Product Name": p["ProductName"], "Category": p["Category"],
                "Sub-Category": p["Subcategory"], "Quantity": "1", "Unit Price": money(price),
                "Unit Cost": money(year_cost(price, p["ListMargin"])), "Discount": "0%", "Line Total": money(price)})
    raw = pd.concat([raw, pd.DataFrame(test_rows)], ignore_index=True)
    issues["test_account_lines"] = len(test_rows)

    # 5) exact duplicate rows (export re-sent a batch)
    dup_idx = rng.choice(n, size=int(n * 0.005), replace=False)
    raw = pd.concat([raw, raw.loc[dup_idx]], ignore_index=True)
    issues["exact_duplicate_rows"] = len(dup_idx)

    # shuffle within the export to mimic an unsorted extract
    raw = raw.sample(frac=1.0, random_state=int(rng.integers(1_000_000))).reset_index(drop=True)
    issues["open_order_lines_blank_ship_date"] = int(open_mask.sum())
    return raw, issues


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--output-dir", default=str(Path(__file__).resolve().parents[1] / "data" / "raw"))
    args = ap.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    products = build_products(rng)
    customers = build_customers(rng)
    lines = simulate_orders(rng, products, customers)
    targets = build_targets(rng, lines, products, customers)
    raw, issues = build_raw_export(rng, lines, products, customers)

    # Masters as delivered by source systems (current list price = 2025 price)
    pm = products[["ProductID", "ProductName", "Category", "Subcategory", "Brand"]].copy()
    pm["ListPrice"] = products["BaseListPrice2022"].map(lambda p: year_price(p, 2025))
    pm["StandardCost"] = [year_cost(lp, m) for lp, m in zip(pm["ListPrice"], products["ListMargin"])]
    pm.to_csv(out / "product_master.csv", index=False)

    cm = customers[["CustomerID", "CustomerName", "Segment", "City", "State", "Region", "CustomerSince"]].copy()
    cm["CustomerSince"] = pd.to_datetime(cm["CustomerSince"]).dt.strftime("%Y-%m-%d")
    cm.to_csv(out / "customer_master.csv", index=False)

    geo = pd.DataFrame(CITIES, columns=["City", "State", "StateCode", "Region", "Latitude", "Longitude", "MarketWeight"])
    geo.drop(columns="MarketWeight").to_csv(out / "geography_reference.csv", index=False)

    raw.to_csv(out / "orders_export_2023_2025.csv", index=False)

    # Finance sends targets as an Excel workbook; one region label uses a legacy spelling
    targets.loc[targets["Region"] == "Midwest", "Region"] = np.where(
        rng.random((targets["Region"] == "Midwest").sum()) < 0.25, "Mid-West", "Midwest")
    with pd.ExcelWriter(out / "sales_targets_2023_2025.xlsx", engine="openpyxl") as xw:
        targets.to_excel(xw, sheet_name="Targets", index=False)
        pd.DataFrame({"Note": [
            f"Synthetic sales plan for {COMPANY}.",
            "Targets = prior-year net sales by Region x Category x Channel x (1 + planned growth),",
            "phased by the prior year's monthly sales profile. Amounts in USD, net of discounts.",
        ]}).to_excel(xw, sheet_name="ReadMe", index=False)

    print(f"Seed {args.seed} -> {out}")
    print(f"  order lines exported : {len(raw):,} (incl. injected issues)")
    print(f"  products / customers : {len(pm)} / {len(cm)}")
    print(f"  target rows          : {len(targets):,}")
    for k, v in issues.items():
        print(f"  issue {k:<34}: {v}")


if __name__ == "__main__":
    main()
