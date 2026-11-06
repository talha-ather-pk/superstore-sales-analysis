# DAX measures

Create a blank table called `_Measures` (Home → Enter data → name it, delete the column after adding the first measure) and add these measures to it. Set the format shown in brackets.

## Core KPIs

```DAX
Total Sales = SUM ( fact_sales[sales] )                                   -- [Currency, 0 dp]

Total Profit = SUM ( fact_sales[profit] )                                 -- [Currency, 0 dp]

Profit Margin % = DIVIDE ( [Total Profit], [Total Sales] )                -- [Percentage, 1 dp]

Orders = DISTINCTCOUNT ( fact_sales[order_id] )                           -- [Whole number]

Units Sold = SUM ( fact_sales[order_quantity] )                           -- [Whole number]

Avg Order Value = DIVIDE ( [Total Sales], [Orders] )                      -- [Currency, 0 dp]

Customers = DISTINCTCOUNT ( fact_sales[customer_key] )                    -- [Whole number]

Avg Discount % = AVERAGE ( fact_sales[discount] )                         -- [Percentage, 1 dp]

Shipping Cost = SUM ( fact_sales[shipping_cost] )                         -- [Currency, 0 dp]

Avg Days to Ship = AVERAGE ( fact_sales[days_to_ship] )                   -- [Decimal, 1 dp]
```

## Time intelligence (needs dim_date marked as date table)

```DAX
Sales PY =
CALCULATE ( [Total Sales], SAMEPERIODLASTYEAR ( dim_date[date] ) )

Sales YoY % =
DIVIDE ( [Total Sales] - [Sales PY], [Sales PY] )                         -- [Percentage, 1 dp]

Profit PY =
CALCULATE ( [Total Profit], SAMEPERIODLASTYEAR ( dim_date[date] ) )

Profit YoY % =
DIVIDE ( [Total Profit] - [Profit PY], [Profit PY] )

Sales YTD =
TOTALYTD ( [Total Sales], dim_date[date] )

Sales Rolling 3M =
CALCULATE (
    [Total Sales],
    DATESINPERIOD ( dim_date[date], MAX ( dim_date[date] ), -3, MONTH )
)
```

## Profitability

```DAX
Loss Lines =
CALCULATE ( COUNTROWS ( fact_sales ), fact_sales[is_loss] = TRUE () )

Loss Lines % =
DIVIDE ( [Loss Lines], COUNTROWS ( fact_sales ) )                         -- [Percentage, 1 dp]

Loss Amount =
CALCULATE ( [Total Profit], fact_sales[is_loss] = TRUE () )               -- [Currency, 0 dp]

Profit Rank (Sub-Category) =
RANKX ( ALL ( dim_product[product_sub_category] ), [Total Profit], , DESC )
```

## Customers

```DAX
Top 20% Customer Sales Share =
VAR CustomerCount = COUNTROWS ( ALL ( dim_customer ) )
VAR TopN_Customers =
    TOPN ( ROUND ( CustomerCount * 0.2, 0 ), ALL ( dim_customer ), [Total Sales], DESC )
RETURN
    DIVIDE (
        CALCULATE ( [Total Sales], TopN_Customers ),
        CALCULATE ( [Total Sales], ALL ( dim_customer ) )
    )                                                                     -- [Percentage, 1 dp]
```

## Conditional formatting helper

```DAX
Margin Color =
SWITCH (
    TRUE (),
    [Profit Margin %] < 0,    "#C0392B",   -- loss: red
    [Profit Margin %] < 0.08, "#E67E22",   -- weak: orange
    "#1E8449"                              -- healthy: green
)
```
Use it in Format → Data colors → fx → Field value → `Margin Color`.

## Checks after building (should match the Python output)

| Measure | Expected (no filters) |
|---|---|
| Total Sales | 14,915,601 |
| Total Profit | 1,521,768 |
| Profit Margin % | 10.2% |
| Orders | 5,496 |
| Loss Lines % | 50.8% |
