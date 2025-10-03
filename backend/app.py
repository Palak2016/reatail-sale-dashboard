from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import math


app = Flask(__name__)
CORS(app)

CSV_PATH = "../daata/sales_data_sample.csv"

def load_data(path=CSV_PATH):
    """
    Load CSV into pandas DataFrame.
    Compute revenue, profit, discount and ensure datatypes.
    """
    try:
        # FIX A: The corrected file path
        df = pd.read_csv(path, parse_dates=['ORDERDATE'])
    except FileNotFoundError:
        cols = [
            'ORDERNUMBER','QUANTITYORDERED','PRICEEACH','ORDERLINENUMBER','SALES',
            'ORDERDATE','STATUS','QTR_ID','MONTH_ID','YEAR_ID','PRODUCTLINE','MSRP',
            'PRODUCTCODE','CUSTOMERNAME','PHONE','ADDRESSLINE1','ADDRESSLINE2','CITY',
            'STATE','POSTALCODE','COUNTRY','TERRITORY','CONTACTLASTNAME',
            'CONTACTFIRSTNAME','DEALSIZE'
        ]
        df = pd.DataFrame(columns=cols)
        df['ORDERDATE'] = pd.to_datetime(df['ORDERDATE'])
        return df # Returns an empty DataFrame if file not found

    numeric_cols = ['QUANTITYORDERED', 'PRICEEACH', 'SALES', 'MSRP']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Derived columns
    df['revenue'] = df['SALES']
    df['discount'] = (df['MSRP'] - df['PRICEEACH']) / df['MSRP']
    df['discount'] = df['discount'].fillna(0).clip(lower=0)

    df['cost_per_unit'] = df['MSRP'] * 0.6
    df['profit'] = df['revenue'] - (df['QUANTITYORDERED'] * df['cost_per_unit'])

    return df # <--- FIX B: MUST explicitly return df here

df=load_data()

def parse_date(s):
    """Convert string to pandas.Timestamp or None."""
    if not s:
        return None
    try:
        return pd.to_datetime(s)
    except Exception:
        return None
    
# CODE FROM app.py
def filter_df(d, start=None, end=None, region=None, product_code=None):
    """
    Filters by start/end date, TERRITORY as region, product_code.
    """
    out = d
    if start:
        start_dt = parse_date(start)
        if start_dt is not None:
            out = out[out['ORDERDATE'] >= start_dt]
    if end:
        end_dt = parse_date(end)
        if end_dt is not None:
            out = out[out['ORDERDATE'] <= end_dt]
    if region:
        # NOTE: Using .copy() is sometimes safer here but not required to fix the NoneType error
        out = out[out['TERRITORY'].astype(str).str.lower() == region.lower()]
    if product_code:
        out = out[out['PRODUCTCODE'].astype(str) == str(product_code)]
    
    return out  # <--- THIS MUST BE HERE AND ALIGNED WITH 'out = d'

@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/api/reload", methods=["POST"])
def reload_data():
    global df
    df = load_data()
    return jsonify({"status": "reloaded", "rows": int(df.shape[0])})

@app.route("/api/kpis")
def kpis():
    start = request.args.get('start')
    end = request.args.get('end')
    region = request.args.get('region')
    product_code = request.args.get('product_code')

    d = filter_df(df, start=start, end=end, region=region, product_code=product_code)

    total_revenue = float(d['revenue'].sum()) if not d.empty else 0.0
    total_orders = int(d['ORDERNUMBER'].nunique()) if not d.empty else 0
    total_units = int(d['QUANTITYORDERED'].sum()) if not d.empty else 0
    gross_profit = float(d['profit'].sum()) if not d.empty else 0.0
    aov = (total_revenue / total_orders) if total_orders else 0.0
    profit_margin = (gross_profit / total_revenue) if total_revenue else 0.0

    return jsonify({
        "total_revenue": round(total_revenue, 2),
        "total_orders": total_orders,
        "total_units_sold": total_units,
        "gross_profit": round(gross_profit, 2),
        "average_order_value": round(aov, 2),
        "profit_margin": round(profit_margin, 4)
    })

# ---------------- Monthly Revenue ----------------
@app.route("/api/monthly-revenue")
def monthly_revenue():
    start = request.args.get('start')
    end = request.args.get('end')
    region = request.args.get('region')
    product_code = request.args.get('product_code')

    d = filter_df(df, start=start, end=end, region=region, product_code=product_code)
    if d.empty:
        return jsonify([])

    monthly = d.groupby(pd.Grouper(key='ORDERDATE', freq='M'))['revenue'].sum().reset_index()
    monthly['month'] = monthly['ORDERDATE'].dt.strftime('%Y-%m')
    result = monthly[['month', 'revenue']].to_dict(orient='records')

    for r in result:
        r['revenue'] = round(float(r['revenue']), 2)
    return jsonify(result)

# ---------------- Top Products ----------------
@app.route("/api/top-products")
def top_products():
    limit = int(request.args.get('limit', 5))
    start = request.args.get('start')
    end = request.args.get('end')
    region = request.args.get('region')

    d = filter_df(df, start=start, end=end, region=region)
    if d.empty:
        return jsonify([])

    agg = d.groupby(['PRODUCTCODE', 'PRODUCTLINE']).agg(
        revenue=('revenue', 'sum'),
        units_sold=('QUANTITYORDERED', 'sum')
    ).reset_index().sort_values('revenue', ascending=False).head(limit)

    out = []
    for _, row in agg.iterrows():
        out.append({
            "product_code": row['PRODUCTCODE'],
            "product_line": row['PRODUCTLINE'],
            "revenue": round(float(row['revenue']), 2),
            "units_sold": int(row['units_sold'])
        })
    return jsonify(out)

# ---------------- Region Sales ----------------
@app.route("/api/region-sales")
def region_sales():
    start = request.args.get('start')
    end = request.args.get('end')

    d = filter_df(df, start=start, end=end)
    if d.empty:
        return jsonify([])

    agg = d.groupby('TERRITORY').agg(revenue=('revenue','sum')).reset_index().sort_values('revenue', ascending=False)

    out = []
    for _, row in agg.iterrows():
        out.append({
            "region": row['TERRITORY'],
            "revenue": round(float(row['revenue']), 2)
        })
    return jsonify(out)

# ---------------- Sales List ----------------
@app.route("/api/sales")
def sales_list():
    start = request.args.get('start')
    end = request.args.get('end')
    region = request.args.get('region')
    product_code = request.args.get('product_code')
    page = max(1, int(request.args.get('page', 1)))
    page_size = max(1, int(request.args.get('page_size', 20)))

    d = filter_df(df, start=start, end=end, region=region, product_code=product_code).copy()
    total = int(d.shape[0])

    if 'ORDERDATE' in d.columns:
        d = d.sort_values('ORDERDATE', ascending=False)

    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    page_df = d.iloc[start_idx:end_idx]
    rows = page_df.to_dict(orient='records')

    for r in rows:
        if 'revenue' in r and r['revenue'] is not None:
            r['revenue'] = round(float(r['revenue']), 2)
        if 'profit' in r and r['profit'] is not None:
            r['profit'] = round(float(r['profit']), 2)
        if 'discount' in r and r['discount'] is not None:
            r['discount'] = round(float(r['discount']), 4)

    return jsonify({
        "page": page,
        "page_size": page_size,
        "total_rows": total,
        "rows": rows
    })

if __name__ == "__main__":
    app.run(debug=True)