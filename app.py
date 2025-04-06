from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import psycopg2
import os
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Database configuration
DB_HOST = "34.148.223.31"
DB_PORT = "5432"
DB_NAME = "proj1part2"
DB_USER = "hg2736"
DB_PASSWORD = "008096"  # Correct password from CountRecords.py
DB_SCHEMA = "hg2736"

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    conn.set_session(autocommit=True)
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/debug_tables')
def debug_tables():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'hg2736'
        """)
        tables = cur.fetchall()
        
        results = {}
        for table in tables:
            table_name = table[0]
            cur.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'hg2736' AND table_name = '{table_name}'
            """)
            columns = cur.fetchall()
            results[table_name] = columns
        
        cur.close()
        conn.close()
        return jsonify({"tables": [t[0] for t in tables], "schema": {k: [{"name": c[0], "type": c[1]} for c in v] for k, v in results.items()}})
    except Exception as e:
        return jsonify({"error": str(e), "traceback": traceback.format_exc()})

@app.route('/etfs')
def list_etfs():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT e.etf_ticker, e.etf_name, e.inception_date, e.aum, f.fund_name as fund_family
            FROM ETF e
            JOIN Fund_has_ETF fe ON e.etf_ticker = fe.etf_ticker
            JOIN Fund_Family f ON fe.fund_id = f.fund_id
            ORDER BY e.etf_ticker
        """)
        etfs = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('etfs.html', etfs=etfs)
    except Exception as e:
        return f"<h1>Error</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>"

@app.route('/etf/<etf_ticker>')
def etf_details(etf_ticker):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get ETF basic info
        cur.execute("""
            SELECT e.*, f.fund_name as fund_family
            FROM ETF e
            JOIN Fund_has_ETF fe ON e.etf_ticker = fe.etf_ticker
            JOIN Fund_Family f ON fe.fund_id = f.fund_id
            WHERE e.etf_ticker = %s
        """, (etf_ticker,))
        etf = cur.fetchone()
        
        # Get sectors
        cur.execute("""
            SELECT s.sector_name
            FROM ETF_has_Sector es
            JOIN Sector s ON es.sector_id = s.sector_id
            WHERE es.etf_ticker = %s
        """, (etf_ticker,))
        sectors = cur.fetchall()
        
        # Get stocks
        cur.execute("""
            SELECT s.stock_ticker, s.stock_name, sie.stock_weight
            FROM Stock_in_ETF sie
            JOIN Stock s ON sie.stock_ticker = s.stock_ticker
            WHERE sie.etf_ticker = %s
            ORDER BY sie.stock_weight DESC
        """, (etf_ticker,))
        stocks = cur.fetchall()
        
        cur.close()
        conn.close()
        return render_template('etf_details.html', etf=etf, sectors=sectors, stocks=stocks)
    except Exception as e:
        return f"<h1>Error</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>"

@app.route('/stocks')
def list_stocks():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT s.stock_ticker, s.stock_name, s.ipo_date, s.stock_sector
            FROM Stock s
            ORDER BY s.stock_ticker
        """)
        stocks = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('stocks.html', stocks=stocks)
    except Exception as e:
        return f"<h1>Error</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>"

@app.route('/stock/<stock_ticker>')
def stock_details(stock_ticker):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get stock basic info
        cur.execute("""
            SELECT *
            FROM Stock
            WHERE stock_ticker = %s
        """, (stock_ticker,))
        stock = cur.fetchone()
        
        # Get ETFs containing this stock
        cur.execute("""
            SELECT e.etf_ticker, e.etf_name, sie.stock_weight
            FROM Stock_in_ETF sie
            JOIN ETF e ON sie.etf_ticker = e.etf_ticker
            WHERE sie.stock_ticker = %s
            ORDER BY sie.stock_weight DESC
        """, (stock_ticker,))
        etfs = cur.fetchall()
        
        cur.close()
        conn.close()
        return render_template('stock_details.html', stock=stock, etfs=etfs)
    except Exception as e:
        return f"<h1>Error</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>"

@app.route('/debug_etf')
def debug_etf():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # First check if the ETF table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'hg2736' AND table_name = 'etf'
            )
        """)
        etf_exists = cur.fetchone()[0]
        
        if not etf_exists:
            # Check for case-sensitive variations
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'hg2736' AND table_name ILIKE 'etf'
            """)
            etf_tables = cur.fetchall()
            return jsonify({"etf_exists": etf_exists, "similar_tables": [t[0] for t in etf_tables]})
        
        # If ETF exists, get its columns
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'hg2736' AND table_name = 'etf'
        """)
        columns = cur.fetchall()
        
        # Get sample data
        cur.execute("SELECT * FROM etf LIMIT 5")
        sample_data = cur.fetchall()
        
        cur.close()
        conn.close()
        return jsonify({
            "etf_exists": etf_exists,
            "columns": [{"name": c[0], "type": c[1]} for c in columns],
            "sample_data": [dict(zip([c[0] for c in columns], row)) for row in sample_data] if sample_data else []
        })
    except Exception as e:
        return jsonify({"error": str(e), "traceback": traceback.format_exc()})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8111) 