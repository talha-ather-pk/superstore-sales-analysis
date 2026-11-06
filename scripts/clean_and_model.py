"""
Superstore Sales: data cleaning and star-schema build for Power BI.

Input : data_raw/superstore_sales_raw.csv  (Tableau "Superstore Sales" sample, Canada, 2009-2012)
Output: data_clean/  fact_sales.csv, dim_date.csv, dim_customer.csv, dim_product.csv,
        dim_geography.csv, data_quality_log.csv
Run   : python scripts/clean_and_model.py   (from the project root)
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data_raw" / "superstore_sales_raw.csv"
OUT = ROOT / "data_clean"
OUT.mkdir(exist_ok=True)

log = []  # data quality log: (check, rows_affected, action)


def note(check, n, action):
    log.append({"check": check, "rows_affected": int(n), "action": action})
    print(f"[DQ] {check}: {n} rows -> {action}")


# 1. Load ---------------------------------------------------------------
df = pd.read_csv(RAW, encoding="latin1")
note("rows loaded", len(df), "none")

# 2. Standardise column names -------------------------------------------
df.columns = (df.columns.str.strip().str.lower()
              .str.replace(r"[^a-z0-9]+", "_", regex=True).str.strip("_"))

# 3. Trim text and fix spelling errors in geography ---------------------
text_cols = [c for c in df.columns if pd.api.types.is_string_dtype(df[c])]
for c in text_cols:
    df[c] = df[c].astype("string").str.strip().str.replace(r"\s+", " ", regex=True)

fixes = {"province": {"Saskachewan": "Saskatchewan",
                      "Newfoundland": "Newfoundland and Labrador"},
         "region": {"Prarie": "Prairie"}}
for col, mapping in fixes.items():
    n = df[col].isin(mapping.keys()).sum()
    df[col] = df[col].replace(mapping)
    note(f"misspelled/legacy values in {col}", n, f"renamed {mapping}")

# 4. Parse dates and validate -------------------------------------------
for c in ["order_date", "ship_date"]:
    df[c] = pd.to_datetime(df[c], format="%m/%d/%Y", errors="coerce")
    note(f"unparseable {c}", df[c].isna().sum(), "checked (none expected)")

df["days_to_ship"] = (df["ship_date"] - df["order_date"]).dt.days
bad_ship = df["days_to_ship"] < 0
note("ship date before order date", bad_ship.sum(), "flagged, days_to_ship set to null")
df.loc[bad_ship, "days_to_ship"] = pd.NA
df["days_to_ship"] = df["days_to_ship"].astype("Int64")

# 5. Duplicates ---------------------------------------------------------
dups = df.duplicated(subset=[c for c in df.columns if c != "row_id"])
note("exact duplicate lines (ignoring row_id)", dups.sum(), "dropped")
df = df[~dups]

# 6. Missing values -----------------------------------------------------
miss = df["product_base_margin"].isna()
note("missing product_base_margin", miss.sum(),
     "filled with median margin of the same sub-category")
df["product_base_margin"] = df.groupby("product_sub_category")["product_base_margin"] \
    .transform(lambda s: s.fillna(s.median()))

# 7. Range checks -------------------------------------------------------
note("negative sales", (df["sales"] < 0).sum(), "checked (none expected)")
note("discount outside 0-100%", (~df["discount"].between(0, 1)).sum(), "checked")
note("loss-making order lines (profit < 0)", (df["profit"] < 0).sum(),
     "kept (real business losses), flagged with is_loss")
df["is_loss"] = df["profit"] < 0

# Outliers: very large orders, kept but flagged (IQR rule on sales)
q1, q3 = df["sales"].quantile([0.25, 0.75])
upper = q3 + 3 * (q3 - q1)
df["is_large_order"] = df["sales"] > upper
note(f"large orders (sales > {upper:,.0f}, 3xIQR)", df["is_large_order"].sum(),
     "kept, flagged with is_large_order")

# Consistency checks that shape the model
multi_seg = df.groupby("customer_name")["customer_segment"].nunique().gt(1).sum()
note("customers appearing under more than one segment", multi_seg,
     "segment kept on the fact table (segment at time of order), not on dim_customer")
multi_cust = df.groupby("order_id")["customer_name"].nunique().gt(1).sum()
note("order IDs shared by more than one customer", multi_cust,
     "kept; order counts use DISTINCTCOUNT(order_id) and are noted as approximate")
attr_var = df.groupby("product_name")[["product_container", "product_base_margin"]] \
    .nunique().gt(1).any(axis=1).sum()
note("products with varying container/base margin", attr_var,
     "dim_product uses the most common value per product")

# 8. Dimensions ---------------------------------------------------------
dim_customer = (df[["customer_name"]].drop_duplicates().sort_values("customer_name")
                .reset_index(drop=True))
dim_customer.insert(0, "customer_key", dim_customer.index + 1)

mode = lambda x: x.mode().iloc[0]
dim_product = (df.groupby("product_name", as_index=False)
               .agg(product_category=("product_category", mode),
                    product_sub_category=("product_sub_category", mode),
                    product_container=("product_container", mode),
                    product_base_margin=("product_base_margin", mode))
               .sort_values("product_name").reset_index(drop=True))
dim_product.insert(0, "product_key", dim_product.index + 1)

dim_geo = (df[["province", "region"]].drop_duplicates()
           .sort_values(["region", "province"]).reset_index(drop=True))
dim_geo.insert(0, "geo_key", dim_geo.index + 1)
dim_geo["country"] = "Canada"

dates = pd.date_range(df["order_date"].min().replace(month=1, day=1),
                      df["ship_date"].max().replace(month=12, day=31), freq="D")
dim_date = pd.DataFrame({"date": dates})
dim_date["year"] = dim_date["date"].dt.year
dim_date["quarter"] = "Q" + dim_date["date"].dt.quarter.astype(str)
dim_date["month_num"] = dim_date["date"].dt.month
dim_date["month"] = dim_date["date"].dt.strftime("%b")
dim_date["year_month"] = dim_date["date"].dt.strftime("%Y-%m")
dim_date["weekday"] = dim_date["date"].dt.strftime("%a")
dim_date["is_weekend"] = dim_date["date"].dt.day_of_week >= 5

# 9. Fact table ---------------------------------------------------------
fact = (df.merge(dim_customer[["customer_key", "customer_name"]], on="customer_name")
          .merge(dim_product[["product_key", "product_name"]], on="product_name")
          .merge(dim_geo[["geo_key", "province", "region"]], on=["province", "region"]))
assert len(fact) == len(df), "row count changed during key lookup"
fact = fact[["row_id", "order_id", "order_date", "ship_date", "customer_key", "product_key",
             "geo_key", "customer_segment", "order_priority", "ship_mode", "order_quantity", "unit_price",
             "discount", "sales", "profit", "shipping_cost", "days_to_ship",
             "is_loss", "is_large_order"]].sort_values("row_id")

# 10. Export ------------------------------------------------------------
for name, t in {"fact_sales": fact, "dim_customer": dim_customer, "dim_product": dim_product,
                "dim_geography": dim_geo, "dim_date": dim_date}.items():
    t.to_csv(OUT / f"{name}.csv", index=False, date_format="%Y-%m-%d")
    print(f"wrote {name}.csv  ({len(t):,} rows)")
pd.DataFrame(log).to_csv(OUT / "data_quality_log.csv", index=False)

print(f"\nTotal sales  : {fact['sales'].sum():,.2f}")
print(f"Total profit : {fact['profit'].sum():,.2f}")
print(f"Orders       : {fact['order_id'].nunique():,}")
