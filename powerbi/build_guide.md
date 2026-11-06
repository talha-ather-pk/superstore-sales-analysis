# Power BI build guide

> The finished dashboard is already in `Superstore.pbip` (open it and click Refresh). This guide is for rebuilding it by hand, e.g. to practise or to adapt it to another dataset.

Time needed: about 3 to 4 hours for a first build.

## 1. Load the data

1. Power BI Desktop → Get data → Text/CSV → load the five files in `data_clean/` (not the data quality log).
2. In Power Query, check the types:
   - `fact_sales`: order_date and ship_date = Date; sales, profit, unit_price, discount, shipping_cost = Decimal; is_loss, is_large_order = True/False.
   - `dim_date`: date = Date.
3. Close & Apply.

## 2. Model (star schema)

Model view → create these relationships (all many-to-one, single direction, from fact to dimension):

| From (many) | To (one) |
|---|---|
| fact_sales[order_date] | dim_date[date] |
| fact_sales[customer_key] | dim_customer[customer_key] |
| fact_sales[product_key] | dim_product[product_key] |
| fact_sales[geo_key] | dim_geography[geo_key] |

Then:
- Select `dim_date` → Table tools → **Mark as date table** → column `date`.
- `dim_date[month]` → Sort by column → `month_num`.
- Hide all key columns (customer_key, product_key, geo_key) and the raw fact columns that have measures, so report users only see clean fields.
- `dim_geography[province]` → Data category → State or Province. `country` → Country.

Take a screenshot of the model view. It goes in the portfolio.

## 3. Measures

Add everything in `dax_measures.md`. Check the totals table at the bottom before building visuals.

## 4. Report pages

Theme: View → Themes → pick a clean one (e.g. "Executive") or set two colours: one main colour, one for losses (red). Keep the same layout on every page: title top-left, slicers in a row under it, KPI cards, then visuals.

Slicers on every page (use View → Sync slicers): **Year**, **Region**, **Customer Segment**, **Product Category**.

### Page 1: Executive Overview
- KPI cards: Total Sales, Total Profit, Profit Margin %, Orders, Avg Order Value. Add Sales YoY % as the card's reference label.
- Line chart: Total Sales and Total Profit by `dim_date[year_month]`.
- Clustered bar: Total Sales by Product Category, with Profit Margin % in the tooltip.
- Filled map: Total Sales by Province (colour by Profit Margin %).
- Donut: Total Sales by Customer Segment.

### Page 2: Product Profitability
- Bar chart: Total Profit by product_sub_category, sorted ascending, bars coloured with `Margin Color`. Tables, Bookcases, Scissors and Rubber Bands will show red.
- Scatter: X = Total Sales, Y = Profit Margin %, details = product_sub_category, size = Units Sold. Add a constant line at 0% on Y.
- Matrix: rows = category → sub-category, values = Sales, Profit, Margin %, Loss Lines %. Conditional formatting on Margin %.
- Card: Loss Amount.

### Page 3: Discounts & Shipping
- Column chart: Profit Margin % by discount band. Create the band in Power Query or as a calculated column:
  ```DAX
  Discount Band =
  SWITCH ( TRUE (),
      fact_sales[discount] <= 0.03, "0-3%",
      fact_sales[discount] <= 0.06, "4-6%",
      fact_sales[discount] <= 0.09, "7-9%",
      "10%+" )
  ```
- Clustered bar: Sales and Profit Margin % by ship_mode.
- Table: Avg Days to Ship by order_priority and ship_mode.
- Card: Shipping Cost.

### Page 4: Customers
- Table: Top 15 customers (Top N filter on customer_name by Total Sales), with Sales, Profit, Margin %, Orders.
- Card: Top 20% Customer Sales Share.
- Bar: Customers by segment.

## 5. Finishing touches (what makes it look professional)
- Tooltips on every visual show Sales, Profit and Margin %.
- One short insight text box per page (see README key findings), e.g. "Furniture is 35% of sales but earns a 2.3% margin."
- Page navigator buttons across the top (Insert → Buttons → Navigator → Page navigator).
- Turn off visual headers you don't need, and align everything (Format → Align).

## 6. Publish
- Save as `superstore_sales_dashboard.pbix`.
- Export screenshots of each page at full size (File → Export → PDF is also fine).
- Optional: Publish to web from Power BI Service gives a public link for your portfolio. Only use it for public data like this.
