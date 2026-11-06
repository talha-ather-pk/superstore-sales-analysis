"""
Superstore Sales: generate the Power BI dashboard as a Power BI Project (PBIP).

Writes powerbi/Superstore.pbip with
  Superstore.SemanticModel/  star schema, relationships, DAX measures (TMDL)
  Superstore.Report/         4 report pages (PBIR JSON)
Open the .pbip in Power BI Desktop, click Refresh, then File > Save as .pbix if a
single file is needed.

Run: python scripts/build_pbip.py   (from the project root)
"""
import json
import shutil
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PBI = ROOT / "powerbi"
NAME = "Superstore"
SM = PBI / f"{NAME}.SemanticModel"
RP = PBI / f"{NAME}.Report"
DATA_FOLDER = str(ROOT / "data_clean") + "\\"
BASE_THEME = "CY26SU04"
THEME_SRC = Path(r"C:\Program Files\Microsoft Power BI Desktop\bin\WebView2Resources"
                 r"\minerva\sharedresources\BaseThemes") / f"{BASE_THEME}.json"

SCHEMA = "https://developer.microsoft.com/json-schemas/fabric"
V_VISUAL, V_PAGE, V_REPORT = "2.4.0", "2.0.0", "3.0.0"

BLUE, RED, ORANGE, GREEN, DARK, GREY = "#2563EB", "#C0392B", "#E67E22", "#1E8449", "#111827", "#6B7280"


def gid(*parts):
    """Deterministic GUID so re-running the script gives a stable diff."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "superstore/" + "/".join(parts)))


def hid(*parts):
    return gid(*parts).replace("-", "")[:20]


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path, obj):
    write(path, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


# =========================================================================
# Semantic model (TMDL)
# =========================================================================
# (name, tmdl dataType, M type, hidden, extra properties)
TABLES = {
    "fact_sales": [
        ("row_id", "int64", "Int64.Type", True, {}),
        ("order_id", "int64", "Int64.Type", False, {}),
        ("order_date", "dateTime", "type date", False, {"formatString": "Short Date"}),
        ("ship_date", "dateTime", "type date", False, {"formatString": "Short Date"}),
        ("customer_key", "int64", "Int64.Type", True, {}),
        ("product_key", "int64", "Int64.Type", True, {}),
        ("geo_key", "int64", "Int64.Type", True, {}),
        ("customer_segment", "string", "type text", False, {}),
        ("order_priority", "string", "type text", False, {}),
        ("ship_mode", "string", "type text", False, {}),
        ("order_quantity", "int64", "Int64.Type", True, {}),
        ("unit_price", "double", "type number", True, {}),
        ("discount", "double", "type number", True, {}),
        ("sales", "double", "type number", True, {}),
        ("profit", "double", "type number", True, {}),
        ("shipping_cost", "double", "type number", True, {}),
        ("days_to_ship", "int64", "Int64.Type", True, {}),
        ("is_loss", "boolean", "logical", False, {}),
        ("is_large_order", "boolean", "logical", False, {}),
    ],
    "dim_product": [
        ("product_key", "int64", "Int64.Type", True, {}),
        ("product_name", "string", "type text", False, {}),
        ("product_category", "string", "type text", False, {}),
        ("product_sub_category", "string", "type text", False, {}),
        ("product_container", "string", "type text", False, {}),
        ("product_base_margin", "double", "type number", True, {}),
    ],
    "dim_customer": [
        ("customer_key", "int64", "Int64.Type", True, {}),
        ("customer_name", "string", "type text", False, {}),
    ],
    "dim_geography": [
        ("geo_key", "int64", "Int64.Type", True, {}),
        ("province", "string", "type text", False, {"dataCategory": "StateOrProvince"}),
        ("region", "string", "type text", False, {}),
        ("country", "string", "type text", False, {"dataCategory": "Country"}),
    ],
    "dim_date": [
        ("date", "dateTime", "type date", False, {"formatString": "Short Date", "isKey": None}),
        ("year", "int64", "Int64.Type", False, {}),
        ("quarter", "string", "type text", False, {}),
        ("month_num", "int64", "Int64.Type", True, {}),
        ("month", "string", "type text", False, {"sortByColumn": "month_num"}),
        ("year_month", "string", "type text", False, {}),
        ("weekday", "string", "type text", False, {}),
        ("is_weekend", "boolean", "logical", False, {}),
    ],
}

CALC_COLUMNS = {
    "fact_sales": [
        ("'Discount Band'", "string",
         'SWITCH ( TRUE (), fact_sales[discount] <= 0.03, "0-3%", fact_sales[discount] <= 0.06, '
         '"4-6%", fact_sales[discount] <= 0.09, "7-9%", "10%+" )',
         {"sortByColumn": "'Discount Band Order'"}),
        ("'Discount Band Order'", "int64",
         "SWITCH ( TRUE (), fact_sales[discount] <= 0.03, 1, fact_sales[discount] <= 0.06, 2, "
         "fact_sales[discount] <= 0.09, 3, 4 )",
         {"isHidden": None}),
    ]
}

CUR, PCT, INT, DEC1 = r"\$#,0;(\$#,0);\$#,0", "0.0%;-0.0%;0.0%", "#,0", "#,0.0"
MEASURES = [  # (name, DAX, formatString, folder)
    ("Total Sales", "SUM ( fact_sales[sales] )", CUR, "Core KPIs"),
    ("Total Profit", "SUM ( fact_sales[profit] )", CUR, "Core KPIs"),
    ("Profit Margin %", "DIVIDE ( [Total Profit], [Total Sales] )", PCT, "Core KPIs"),
    ("Orders", "DISTINCTCOUNT ( fact_sales[order_id] )", INT, "Core KPIs"),
    ("Units Sold", "SUM ( fact_sales[order_quantity] )", INT, "Core KPIs"),
    ("Avg Order Value", "DIVIDE ( [Total Sales], [Orders] )", CUR, "Core KPIs"),
    ("Customers", "DISTINCTCOUNT ( fact_sales[customer_key] )", INT, "Core KPIs"),
    ("Avg Discount %", "AVERAGE ( fact_sales[discount] )", PCT, "Core KPIs"),
    ("Shipping Cost", "SUM ( fact_sales[shipping_cost] )", CUR, "Core KPIs"),
    ("Avg Days to Ship", "AVERAGE ( fact_sales[days_to_ship] )", DEC1, "Core KPIs"),
    ("Sales PY", "CALCULATE ( [Total Sales], SAMEPERIODLASTYEAR ( dim_date[date] ) )", CUR,
     "Time intelligence"),
    ("Sales YoY %", "DIVIDE ( [Total Sales] - [Sales PY], [Sales PY] )", PCT, "Time intelligence"),
    ("Profit PY", "CALCULATE ( [Total Profit], SAMEPERIODLASTYEAR ( dim_date[date] ) )", CUR,
     "Time intelligence"),
    ("Profit YoY %", "DIVIDE ( [Total Profit] - [Profit PY], [Profit PY] )", PCT,
     "Time intelligence"),
    ("Sales YTD", "TOTALYTD ( [Total Sales], dim_date[date] )", CUR, "Time intelligence"),
    ("Sales Rolling 3M",
     "CALCULATE ( [Total Sales], DATESINPERIOD ( dim_date[date], MAX ( dim_date[date] ), -3, MONTH ) )",
     CUR, "Time intelligence"),
    ("Loss Lines", "CALCULATE ( COUNTROWS ( fact_sales ), fact_sales[is_loss] = TRUE () )", INT,
     "Profitability"),
    ("Loss Lines %", "DIVIDE ( [Loss Lines], COUNTROWS ( fact_sales ) )", PCT, "Profitability"),
    ("Loss Amount", "CALCULATE ( [Total Profit], fact_sales[is_loss] = TRUE () )", CUR,
     "Profitability"),
    ("Profit Rank (Sub-Category)",
     "RANKX ( ALL ( dim_product[product_sub_category] ), [Total Profit], , DESC )", INT,
     "Profitability"),
    ("Top 20% Customer Sales Share",
     "VAR CustomerCount = COUNTROWS ( ALL ( dim_customer ) ) "
     "VAR TopCustomers = TOPN ( ROUND ( CustomerCount * 0.2, 0 ), ALL ( dim_customer ), [Total Sales], DESC ) "
     "RETURN DIVIDE ( CALCULATE ( [Total Sales], TopCustomers ), CALCULATE ( [Total Sales], ALL ( dim_customer ) ) )",
     PCT, "Customers"),
    ("Margin Color",
     f'SWITCH ( TRUE (), [Profit Margin %] < 0, "{RED}", [Profit Margin %] < 0.08, "{ORANGE}", "{BLUE}" )',
     None, "Formatting"),
]

RELATIONSHIPS = [
    ("fact_sales", "order_date", "dim_date", "date"),
    ("fact_sales", "customer_key", "dim_customer", "customer_key"),
    ("fact_sales", "product_key", "dim_product", "product_key"),
    ("fact_sales", "geo_key", "dim_geography", "geo_key"),
]


def q(name):
    """Quote a TMDL object name when needed."""
    return name if name.replace("_", "").isalnum() else f"'{name}'"


def tmdl_table(table):
    cols = TABLES[table]
    out = [f"table {table}", f"\tlineageTag: {gid(table)}", ""]
    if table == "dim_date":
        out[1:1] = ["\tdataCategory: Time"]
    if table == "fact_sales":
        for name, dax, fmt, folder in MEASURES:
            out.append(f"\tmeasure {q(name)} = {dax}")
            if fmt:
                out.append(f"\t\tformatString: {fmt}")
            out += [f"\t\tdisplayFolder: {folder}", f"\t\tlineageTag: {gid(table, 'm', name)}", ""]
    for name, dtype, _, hidden, extra in cols:
        out += [f"\tcolumn {name}", f"\t\tdataType: {dtype}"]
        if hidden:
            out.append("\t\tisHidden")
        for k, v in extra.items():
            out.append(f"\t\t{k}" if v is None else f"\t\t{k}: {v}")
        if "formatString" not in extra and dtype == "int64":
            out.append("\t\tformatString: 0")
        summ = "sum" if dtype in ("double",) else "none"
        out += [f"\t\tlineageTag: {gid(table, name)}", f"\t\tsummarizeBy: {summ}",
                f"\t\tsourceColumn: {name}", "", "\t\tannotation SummarizationSetBy = Automatic", ""]
    for name, dtype, dax, extra in CALC_COLUMNS.get(table, []):
        out += [f"\tcolumn {name} = {dax}", f"\t\tdataType: {dtype}"]
        for k, v in extra.items():
            out.append(f"\t\t{k}" if v is None else f"\t\t{k}: {v}")
        out += [f"\t\tlineageTag: {gid(table, name)}", "\t\tsummarizeBy: none", "",
                "\t\tannotation SummarizationSetBy = Automatic", ""]

    types = ", ".join(f'{{"{n}", {m}}}' for n, _, m, _, _ in cols if m != "logical")
    bools = [n for n, _, m, _, _ in cols if m == "logical"]
    m = [
        "let",
        f'    Source = Csv.Document(File.Contents(DataFolder & "{table}.csv"), '
        '[Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),',
        "    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),",
        f'    Typed = Table.TransformColumnTypes(Promoted, {{{types}}}, "en-US")'
        + ("," if bools else ""),
    ]
    if bools:
        conv = ", ".join(f'{{"{b}", each _ = "True", type logical}}' for b in bools)
        m.append(f"    Logicals = Table.TransformColumns(Typed, {{{conv}}})")
    m += ["in", "    Logicals" if bools else "    Typed"]
    out += [f"\tpartition {table} = m", "\t\tmode: import", "\t\tsource ="]
    out += ["\t\t\t\t" + line for line in m]
    out += ["", "\tannotation PBI_ResultType = Table", ""]
    return "\n".join(out)


def build_semantic_model():
    if SM.exists():
        shutil.rmtree(SM)
    write_json(SM / "definition.pbism", {
        "$schema": f"{SCHEMA}/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "4.2", "settings": {}})
    write_json(SM / ".platform", {
        "$schema": f"{SCHEMA}/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "SemanticModel", "displayName": NAME},
        "config": {"version": "2.0", "logicalId": gid("sm")}})
    d = SM / "definition"
    write(d / "database.tmdl", "database\n\tcompatibilityLevel: 1600\n\n")
    order = json.dumps(["DataFolder", *TABLES])
    write(d / "model.tmdl", "\n".join([
        "model Model",
        "\tculture: en-US",
        "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
        "\tsourceQueryCulture: en-US",
        "\tdataAccessOptions",
        "\t\tlegacyRedirects",
        "\t\treturnErrorValuesAsNull",
        "",
        f"annotation PBI_QueryOrder = {order}",
        "",
        "annotation __PBI_TimeIntelligenceEnabled = 0",
        "",
        *[f"ref table {t}" for t in TABLES],
        "",
    ]))
    write(d / "expressions.tmdl", "\n".join([
        f'expression DataFolder = "{DATA_FOLDER}" meta [IsParameterQuery = true, Type = "Text", '
        "IsParameterQueryRequired = true]",
        f"\tlineageTag: {gid('DataFolder')}",
        "",
        "\tannotation PBI_ResultType = Text",
        "",
    ]))
    rels = []
    for ft, fc, tt, tc in RELATIONSHIPS:
        rels += [f"relationship {gid('rel', ft, fc)}"]
        if fc == "order_date":
            rels += ["\tjoinOnDateBehavior: datePartOnly"]
        rels += [f"\tfromColumn: {ft}.{fc}", f"\ttoColumn: {tt}.{tc}", ""]
    write(d / "relationships.tmdl", "\n".join(rels))
    for t in TABLES:
        write(d / "tables" / f"{t}.tmdl", tmdl_table(t))


# =========================================================================
# Report (PBIR)
# =========================================================================
def lit(v):
    if isinstance(v, bool):
        s = "true" if v else "false"
    elif isinstance(v, (int, float)):
        s = f"{v}D"
    else:
        s = "'" + str(v).replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": s}}}


def lit_int(v):
    return {"expr": {"Literal": {"Value": f"{v}L"}}}


AXES_CLEAN = {"categoryAxis": [{"properties": {"showAxisTitle": lit(False)}}],
              "valueAxis": [{"properties": {"showAxisTitle": lit(False)}}]}


def col(table, column):
    return {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": column}}


def mea(name, table="fact_sales"):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}}


def ref(field):
    k = next(iter(field))
    return f"{field[k]['Expression']['SourceRef']['Entity']}.{field[k]['Property']}"


def proj(field, display=None):
    p = {"field": field, "queryRef": ref(field), "nativeQueryRef": field[next(iter(field))]["Property"]}
    if display:
        p["displayName"] = display
    return p


def solid(color):
    return {"solid": {"color": lit(color) if isinstance(color, str) else {"expr": color}}}


class Page:
    def __init__(self, key, title, subtitle):
        self.key, self.name = key, hid("page", key)
        self.title, self.subtitle = title, subtitle
        self.visuals = []

    def add(self, vid, x, y, w, h, visual):
        self.visuals.append({
            "$schema": f"{SCHEMA}/item/report/definition/visualContainer/{V_VISUAL}/schema.json",
            "name": hid(self.key, vid),
            "position": {"x": x, "y": y, "z": len(self.visuals) * 1000, "height": h, "width": w,
                         "tabOrder": len(self.visuals) * 1000},
            "visual": visual,
        })


def container(title=None, border=True):
    o = {}
    if title:
        o["title"] = [{"properties": {"show": lit(True), "text": lit(title),
                                      "fontColor": solid(DARK), "fontSize": lit(11), "bold": lit(True)}}]
    else:
        o["title"] = [{"properties": {"show": lit(False)}}]
    o["background"] = [{"properties": {"show": lit(True), "color": solid("#FFFFFF")}}]
    if border:
        o["border"] = [{"properties": {"show": lit(True), "color": solid("#E5E7EB"), "radius": lit(6)}}]
    o["visualHeader"] = [{"properties": {"show": lit(False)}}]
    return o


def textbox(text, size=11, bold=False, color=DARK):
    return {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": [
        {"textRuns": [{"value": text, "textStyle": {
            "fontSize": f"{size}pt", "color": color, **({"fontWeight": "bold"} if bold else {})}}]}]}}]},
        "visualContainerObjects": {"background": [{"properties": {"show": lit(False)}}],
                                   "visualHeader": [{"properties": {"show": lit(False)}}]},
        "drillFilterOtherVisuals": True}


def chart(vtype, roles, title, sort=None, objects=None, border=True):
    v = {"visualType": vtype,
         "query": {"queryState": {r: {"projections": [proj(f) if isinstance(f, dict) else proj(*f)
                                                      for f in fs]} for r, fs in roles.items()}},
         "objects": {**(AXES_CLEAN if vtype in AXIS_VISUALS else {}), **(objects or {})},
         "visualContainerObjects": container(title, border),
         "drillFilterOtherVisuals": True}
    if sort:
        v["query"]["sortDefinition"] = {"sort": [{"field": f, "direction": d} for f, d in sort],
                                        "isDefaultSort": False}
    return v


AXIS_VISUALS = {"lineChart", "clusteredBarChart", "clusteredColumnChart", "scatterChart"}
MILLIONS = {"Total Sales", "Total Profit", "Loss Amount"}


def card(measure, label):
    lab = {"color": solid(DARK), "fontSize": lit(24)}
    if measure in MILLIONS:
        lab.update(labelDisplayUnits=lit(1000000), labelPrecision=lit_int(2))
    return chart("card", {"Values": [(mea(measure), label)]}, None, objects={
        "labels": [{"properties": lab}],
        "categoryLabels": [{"properties": {"show": lit(True), "color": solid(GREY), "fontSize": lit(10)}}]})


def slicer(field, label, group):
    v = chart("slicer", {"Values": [(field, label)]}, label, objects={
        "data": [{"properties": {"mode": lit("Dropdown")}}],
        "header": [{"properties": {"show": lit(False)}}]})
    v["syncGroup"] = {"groupName": group, "fieldChanges": True, "filterChanges": True}
    return v


MARGIN_FILL = {"dataPoint": [{"properties": {"fill": solid(mea("Margin Color"))},
                              "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}}]}


def single_fill(color):
    return {"dataPoint": [{"properties": {"fill": solid(color)}}]}


def labels_on():
    return {"labels": [{"properties": {"show": lit(True)}}]}


def page_frame(p):
    p.add("title", 16, 4, 640, 48, textbox(p.title, 20, True))
    p.add("subtitle", 16, 48, 640, 30, textbox(p.subtitle, 10, False, GREY))
    slicers = [(col("dim_date", "year"), "Year", "year"),
               (col("dim_geography", "region"), "Region", "region"),
               (col("fact_sales", "customer_segment"), "Segment", "segment"),
               (col("dim_product", "product_category"), "Category", "category")]
    for i, (f, label, g) in enumerate(slicers):
        p.add(f"slicer_{g}", 672 + i * 150, 10, 142, 60, slicer(f, label, g))


def build_pages():
    W = 1280
    pages = []

    # ---- 1. Executive overview -------------------------------------------
    p = Page("overview", "Executive Overview",
             "Furniture is 35% of sales but earns only a 2.3% margin.")
    page_frame(p)
    kpis = [("Total Sales", "Total Sales"), ("Total Profit", "Total Profit"),
            ("Profit Margin %", "Profit Margin"), ("Orders", "Orders"),
            ("Avg Order Value", "Avg Order Value")]
    cw = (W - 32 - 4 * 12) / 5
    for i, (m, label) in enumerate(kpis):
        p.add(f"kpi_{i}", 16 + i * (cw + 12), 82, cw, 92, card(m, label))
    p.add("trend", 16, 186, 820, 250, chart(
        "lineChart", {"Category": [(col("dim_date", "year_month"), "Month")],
                      "Y": [mea("Total Sales"), mea("Total Profit")]},
        "Sales and profit by month", sort=[(col("dim_date", "year_month"), "Ascending")]))
    p.add("category", 848, 186, 416, 250, chart(
        "clusteredBarChart", {"Category": [(col("dim_product", "product_category"), "Category")],
                              "Y": [mea("Total Sales")], "Tooltips": [mea("Profit Margin %")]},
        "Sales by category (colour = margin)", sort=[(mea("Total Sales"), "Descending")],
        objects={**MARGIN_FILL, **labels_on()}))
    p.add("province", 16, 448, 820, 262, chart(
        "clusteredBarChart", {"Category": [(col("dim_geography", "province"), "Province")],
                              "Y": [mea("Total Sales")], "Tooltips": [mea("Profit Margin %")]},
        "Sales by province (colour = margin)", sort=[(mea("Total Sales"), "Descending")],
        objects=MARGIN_FILL))
    p.add("segment", 848, 448, 416, 262, chart(
        "donutChart", {"Category": [(col("fact_sales", "customer_segment"), "Segment")], "Y": [mea("Total Sales")]},
        "Sales by customer segment"))
    pages.append(p)

    # ---- 2. Product profitability ----------------------------------------
    p = Page("products", "Product Profitability",
             "Tables and Bookcases are high-volume sub-categories sold at a loss.")
    page_frame(p)
    kpis = [("Total Profit", "Total Profit"), ("Profit Margin %", "Profit Margin"),
            ("Loss Amount", "Loss on loss-making lines"), ("Loss Lines %", "Order lines at a loss")]
    cw = (W - 32 - 3 * 12) / 4
    for i, (m, label) in enumerate(kpis):
        p.add(f"kpi_{i}", 16 + i * (cw + 12), 82, cw, 92, card(m, label))
    p.add("subcat", 16, 186, 560, 524, chart(
        "clusteredBarChart", {"Category": [(col("dim_product", "product_sub_category"), "Sub-category")],
                              "Y": [mea("Total Profit")],
                              "Tooltips": [mea("Total Sales"), mea("Profit Margin %")]},
        "Profit by sub-category", sort=[(mea("Total Profit"), "Ascending")], objects=MARGIN_FILL))
    p.add("scatter", 588, 186, 676, 262, chart(
        "scatterChart", {"Category": [(col("dim_product", "product_sub_category"), "Sub-category")],
                         "X": [mea("Total Sales")], "Y": [mea("Profit Margin %")],
                         "Size": [mea("Units Sold")]},
        "Sales vs margin by sub-category",
        objects={**MARGIN_FILL, "categoryLabels": [{"properties": {"show": lit(True)}}]}))
    p.add("matrix", 588, 460, 676, 250, chart(
        "pivotTable", {"Rows": [(col("dim_product", "product_category"), "Category"),
                                (col("dim_product", "product_sub_category"), "Sub-category")],
                       "Values": [mea("Total Sales"), mea("Total Profit"), mea("Profit Margin %"),
                                  mea("Loss Lines %")]},
        "Category detail"))
    pages.append(p)

    # ---- 3. Discounts & shipping -----------------------------------------
    p = Page("discounts", "Discounts & Shipping",
             "Margin halves above 10% discount; Express Air ships no faster than Regular Air.")
    page_frame(p)
    kpis = [("Avg Discount %", "Avg discount"), ("Shipping Cost", "Shipping cost"),
            ("Avg Days to Ship", "Avg days to ship")]
    cw = (W - 32 - 2 * 12) / 3
    for i, (m, label) in enumerate(kpis):
        p.add(f"kpi_{i}", 16 + i * (cw + 12), 82, cw, 92, card(m, label))
    p.add("band", 16, 186, 620, 262, chart(
        "clusteredColumnChart", {"Category": [(col("fact_sales", "Discount Band"), "Discount band")],
                                 "Y": [mea("Profit Margin %")], "Tooltips": [mea("Total Sales")]},
        "Profit margin by discount band", sort=[(col("fact_sales", "Discount Band"), "Ascending")],
        objects={**MARGIN_FILL, **labels_on()}))
    p.add("shipsales", 648, 186, 616, 262, chart(
        "clusteredBarChart", {"Category": [(col("fact_sales", "ship_mode"), "Ship mode")],
                              "Y": [mea("Total Sales")], "Tooltips": [mea("Profit Margin %")]},
        "Sales by ship mode (colour = margin)", sort=[(mea("Total Sales"), "Descending")],
        objects={**MARGIN_FILL, **labels_on()}))
    p.add("shipmargin", 16, 460, 620, 250, chart(
        "clusteredBarChart", {"Category": [(col("fact_sales", "ship_mode"), "Ship mode")],
                              "Y": [mea("Profit Margin %")]},
        "Profit margin by ship mode", sort=[(mea("Profit Margin %"), "Descending")],
        objects={**MARGIN_FILL, **labels_on()}))
    p.add("days", 648, 460, 616, 250, chart(
        "pivotTable", {"Rows": [(col("fact_sales", "order_priority"), "Priority")],
                       "Columns": [(col("fact_sales", "ship_mode"), "Ship mode")],
                       "Values": [mea("Avg Days to Ship")]},
        "Avg days to ship by priority and ship mode"))
    pages.append(p)

    # ---- 4. Customers ----------------------------------------------------
    p = Page("customers", "Customers",
             "The top 20% of customers bring in 46% of sales; Corporate is the largest segment.")
    page_frame(p)
    kpis = [("Customers", "Customers"), ("Top 20% Customer Sales Share", "Sales from top 20% of customers"),
            ("Avg Order Value", "Avg order value")]
    cw = (W - 32 - 2 * 12) / 3
    for i, (m, label) in enumerate(kpis):
        p.add(f"kpi_{i}", 16 + i * (cw + 12), 82, cw, 92, card(m, label))
    p.add("top", 16, 186, 760, 524, chart(
        "tableEx", {"Values": [(col("dim_customer", "customer_name"), "Customer"), mea("Total Sales"),
                               mea("Total Profit"), mea("Profit Margin %"), mea("Orders")]},
        "Customers ranked by sales", sort=[(mea("Total Sales"), "Descending")]))
    p.add("seg_sales", 788, 186, 476, 262, chart(
        "clusteredBarChart", {"Category": [(col("fact_sales", "customer_segment"), "Segment")],
                              "Y": [mea("Total Sales")], "Tooltips": [mea("Profit Margin %")]},
        "Sales by segment", sort=[(mea("Total Sales"), "Descending")],
        objects={**single_fill(BLUE), **labels_on()}))
    p.add("seg_cust", 788, 460, 476, 250, chart(
        "clusteredBarChart", {"Category": [(col("fact_sales", "customer_segment"), "Segment")],
                              "Y": [mea("Customers")]},
        "Customers by segment", sort=[(mea("Customers"), "Descending")],
        objects={**single_fill(GREY), **labels_on()}))
    pages.append(p)
    return pages


def build_report():
    if RP.exists():
        shutil.rmtree(RP)
    write_json(RP / "definition.pbir", {
        "$schema": f"{SCHEMA}/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0",
        "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}})
    write_json(RP / ".platform", {
        "$schema": f"{SCHEMA}/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "Report", "displayName": NAME},
        "config": {"version": "2.0", "logicalId": gid("report")}})
    theme_dst = RP / "StaticResources" / "SharedResources" / "BaseThemes" / f"{BASE_THEME}.json"
    theme_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(THEME_SRC, theme_dst)

    d = RP / "definition"
    write_json(d / "version.json", {
        "$schema": f"{SCHEMA}/item/report/definition/versionMetadata/1.0.0/schema.json",
        "version": "2.0.0"})
    write_json(d / "report.json", {
        "$schema": f"{SCHEMA}/item/report/definition/report/{V_REPORT}/schema.json",
        "themeCollection": {"baseTheme": {
            "name": BASE_THEME,
            "reportVersionAtImport": {"visual": V_VISUAL, "report": V_REPORT, "page": V_PAGE},
            "type": "SharedResources"}},
        "resourcePackages": [{"name": "SharedResources", "type": "SharedResources", "items": [
            {"name": BASE_THEME, "path": f"BaseThemes/{BASE_THEME}.json", "type": "BaseTheme"}]}],
        "objects": {"outspacePane": [{"properties": {"expanded": lit(False)}}]},
        "settings": {"useStylableVisualContainerHeader": True,
                     "defaultDrillFilterOtherVisuals": True,
                     "allowChangeFilterTypes": True,
                     "useEnhancedTooltips": True}})
    pages = build_pages()
    write_json(d / "pages" / "pages.json", {
        "$schema": f"{SCHEMA}/item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": [p.name for p in pages], "activePageName": pages[0].name})
    for p in pages:
        pd_ = d / "pages" / p.name
        write_json(pd_ / "page.json", {
            "$schema": f"{SCHEMA}/item/report/definition/page/{V_PAGE}/schema.json",
            "name": p.name, "displayName": p.title, "displayOption": "FitToPage",
            "height": 720, "width": W_PAGE,
            "objects": {"background": [{"properties": {"color": solid("#F3F4F6"),
                                                        "transparency": lit(0)}}]}})
        for v in p.visuals:
            write_json(pd_ / "visuals" / v["name"] / "visual.json", v)
    return pages


W_PAGE = 1280

if __name__ == "__main__":
    build_semantic_model()
    pages = build_report()
    write_json(PBI / f"{NAME}.pbip", {
        "$schema": f"{SCHEMA}/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0",
        "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
        "settings": {"enableAutoRecovery": True}})
    write(PBI / ".gitignore", "**/.pbi/localSettings.json\n**/.pbi/cache.abf\n")
    print(f"wrote {PBI / (NAME + '.pbip')}")
    print(f"  semantic model: {len(TABLES)} tables, {len(MEASURES)} measures, "
          f"{len(RELATIONSHIPS)} relationships")
    print(f"  report: {len(pages)} pages, {sum(len(p.visuals) for p in pages)} visuals")
