"""
Superstore Sales: static charts of the key findings for the README.

Input : data_clean/ (run clean_and_model.py first)
Output: images/chart_*.png
Run   : python scripts/make_charts.py   (from the project root)
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, PercentFormatter
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data_clean"
IMG = ROOT / "images"
IMG.mkdir(exist_ok=True)

BLUE, RED, ORANGE, GREY = "#2563EB", "#C0392B", "#E67E22", "#9CA3AF"
plt.rcParams.update({"font.family": "Segoe UI", "font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.titleweight": "bold",
                     "axes.titlesize": 12, "axes.titlelocation": "left"})
money = FuncFormatter(lambda v, _: ("-" if v < 0 else "") +
                      (f"${abs(v)/1e6:.1f}M" if abs(v) >= 1e6 else f"${abs(v)/1e3:.0f}K"))

f = pd.read_csv(CLEAN / "fact_sales.csv", parse_dates=["order_date"])
f = f.merge(pd.read_csv(CLEAN / "dim_product.csv"), on="product_key")


def margin_colour(m):
    return RED if m < 0 else ORANGE if m < 0.08 else BLUE


def save(fig, name):
    fig.tight_layout()
    fig.savefig(IMG / name, dpi=150)
    plt.close(fig)
    print(f"wrote images/{name}")


# 1. Category: share of sales vs margin -----------------------------------
cat = f.groupby("product_category")[["sales", "profit"]].sum()
cat["margin"] = cat.profit / cat.sales
cat = cat.sort_values("sales")
fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.2), sharey=True)
a1.barh(cat.index, cat.sales, color=GREY)
a1.xaxis.set_major_formatter(money)
a1.set_title("Sales")
a2.barh(cat.index, cat.margin, color=[margin_colour(m) for m in cat.margin])
a2.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
a2.set_title("Profit margin")
for y, m in enumerate(cat.margin):
    a2.text(m + 0.003, y, f"{m:.1%}", va="center")
fig.suptitle("Furniture is 35% of sales but earns a 2.3% margin", x=0.01, ha="left",
             fontweight="bold", fontsize=13)
save(fig, "chart_category_margin.png")

# 2. Profit by sub-category ------------------------------------------------
sub = f.groupby("product_sub_category")[["sales", "profit"]].sum()
sub["margin"] = sub.profit / sub.sales
sub = sub.sort_values("profit")
fig, ax = plt.subplots(figsize=(9, 6))
ax.barh(sub.index, sub.profit, color=[margin_colour(m) for m in sub.margin])
ax.axvline(0, color="black", lw=0.8)
ax.xaxis.set_major_formatter(money)
ax.set_title("Profit by sub-category: Tables and Bookcases lose money on high sales")
save(fig, "chart_subcategory_profit.png")

# 3. Margin by discount band -----------------------------------------------
band = pd.cut(f.discount, [-1, 0.03, 0.06, 0.09, 1], labels=["0-3%", "4-6%", "7-9%", "10%+"])
d = f.groupby(band, observed=True)[["sales", "profit"]].sum()
d["margin"] = d.profit / d.sales
fig, ax = plt.subplots(figsize=(7, 3.6))
ax.bar(d.index.astype(str), d.margin, color=[margin_colour(m) for m in d.margin])
ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
for x, m in enumerate(d.margin):
    ax.text(x, m + 0.003, f"{m:.1%}", ha="center")
ax.set_xlabel("Discount")
ax.set_title("Profit margin falls as discounts rise")
save(fig, "chart_discount_margin.png")

# 4. Ship mode: sales, margin and speed ------------------------------------
sm = f.groupby("ship_mode").agg(sales=("sales", "sum"), profit=("profit", "sum"),
                                days=("days_to_ship", "mean"))
sm["margin"] = sm.profit / sm.sales
sm = sm.sort_values("sales")
fig, axes = plt.subplots(1, 3, figsize=(10, 2.8), sharey=True)
axes[0].barh(sm.index, sm.sales, color=GREY)
axes[0].xaxis.set_major_formatter(money)
axes[0].set_title("Sales")
axes[1].barh(sm.index, sm.margin, color=[margin_colour(m) for m in sm.margin])
axes[1].xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
axes[1].set_title("Margin")
axes[2].barh(sm.index, sm.days, color=GREY)
axes[2].set_title("Avg days to ship")
for y, v in enumerate(sm.days):
    axes[2].text(v + 0.05, y, f"{v:.1f}", va="center")
fig.suptitle("Delivery Truck: 42% of sales at a 4.3% margin. Express Air is no faster.",
             x=0.01, ha="left", fontweight="bold", fontsize=13)
save(fig, "chart_ship_mode.png")

# 5. Yearly sales vs orders ------------------------------------------------
y = f.groupby(f.order_date.dt.year).agg(sales=("sales", "sum"), orders=("order_id", "nunique"))
fig, ax = plt.subplots(figsize=(7, 3.6))
ax.bar(y.index.astype(str), y.sales, color=BLUE)
ax.yaxis.set_major_formatter(money)
for x, (s, o) in enumerate(zip(y.sales, y.orders)):
    ax.text(x, s, f"{o:,} orders", ha="center", va="bottom", fontsize=9)
ax.set_title("Sales fell 11.6% from 2009 to 2012 while order counts held steady")
save(fig, "chart_yearly_sales.png")
