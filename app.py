from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import psycopg2
import os
import traceback
from datetime import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
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

# Session configuration
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes

def format_currency(value):
    """Format a number as currency with appropriate suffix (B for billions, M for millions)"""
    if value is None:
        return 'N/A'
    if value >= 1_000_000_000:
        return f"${value/1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"${value/1_000_000:.2f}M"
    else:
        return f"${value:,.2f}"

# Make the function available in templates
app.jinja_env.filters['format_currency'] = format_currency

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

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

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
        
        # Get search parameter if any
        search_query = request.args.get('q', '')
        
        if search_query:
            # Format the search query for tsquery
            # Replace spaces with & to make it an AND search
            formatted_query = ' & '.join(search_query.split())
            
            # Full-text search with ranking across all ETF-related information
            cur.execute("""
                WITH search_results AS (
                    SELECT 
                        e.etf_ticker,
                        e.etf_name,
                        e.inception_date,
                        e.aum,
                        f.fund_name,
                        ts_rank_cd(
                            setweight(to_tsvector('english', COALESCE(e.etf_name, '')), 'A') ||
                            setweight(to_tsvector('english', COALESCE(e.etf_review, '')), 'B') ||
                            setweight(to_tsvector('english', COALESCE(f.fund_name, '')), 'C') ||
                            setweight(to_tsvector('english', COALESCE(string_agg(DISTINCT s.sector_name, ' '), '')), 'D') ||
                            setweight(to_tsvector('english', COALESCE(string_agg(DISTINCT st.stock_name, ' '), '')), 'D') ||
                            setweight(to_tsvector('english', COALESCE(string_agg(DISTINCT ec.comment_text, ' '), '')), 'D') ||
                            setweight(to_tsvector('english', COALESCE(string_agg(DISTINCT cat.category_name, ' '), '')), 'D'),
                            to_tsquery('english', %s)
                        ) as rank
                    FROM ETF e
                    LEFT JOIN fund_has_etf fe ON e.etf_ticker = fe.etf_ticker
                    LEFT JOIN fund_family f ON fe.fund_id = f.fund_id
                    LEFT JOIN ETF_has_Sector es ON e.etf_ticker = es.etf_ticker
                    LEFT JOIN Sector s ON es.sector_id = s.sector_id
                    LEFT JOIN Stock_in_ETF sie ON e.etf_ticker = sie.etf_ticker
                    LEFT JOIN Stock st ON sie.stock_ticker = st.stock_ticker
                    LEFT JOIN ETF_Comments ec ON e.etf_ticker = ec.etf_ticker
                    LEFT JOIN etf_category cat ON e.etf_ticker = cat.etf_ticker
                    GROUP BY e.etf_ticker, e.etf_name, e.inception_date, e.aum, f.fund_name
                    HAVING 
                        to_tsvector('english', COALESCE(e.etf_name, '')) @@ to_tsquery('english', %s) OR
                        to_tsvector('english', COALESCE(e.etf_review, '')) @@ to_tsquery('english', %s) OR
                        to_tsvector('english', COALESCE(f.fund_name, '')) @@ to_tsquery('english', %s) OR
                        to_tsvector('english', COALESCE(string_agg(DISTINCT s.sector_name, ' '), '')) @@ to_tsquery('english', %s) OR
                        to_tsvector('english', COALESCE(string_agg(DISTINCT st.stock_name, ' '), '')) @@ to_tsquery('english', %s) OR
                        to_tsvector('english', COALESCE(string_agg(DISTINCT ec.comment_text, ' '), '')) @@ to_tsquery('english', %s) OR
                        to_tsvector('english', COALESCE(string_agg(DISTINCT cat.category_name, ' '), '')) @@ to_tsquery('english', %s) OR
                        e.etf_ticker ILIKE %s OR
                        CAST(e.aum AS TEXT) ILIKE %s
                )
                SELECT etf_ticker, etf_name, inception_date, aum, fund_name
                FROM search_results
                ORDER BY rank DESC NULLS LAST, etf_ticker
            """, (formatted_query, formatted_query, formatted_query, formatted_query, 
                  formatted_query, formatted_query, formatted_query, formatted_query,
                  '%' + search_query + '%', '%' + search_query + '%'))
        else:
            # If no search query, return all
            cur.execute("""
                SELECT e.etf_ticker, e.etf_name, e.inception_date, e.aum, f.fund_name, e.comment_count
                FROM ETF e
                LEFT JOIN fund_has_etf fe ON e.etf_ticker = fe.etf_ticker
                LEFT JOIN fund_family f ON fe.fund_id = f.fund_id
                ORDER BY e.etf_ticker
            """)
            
        etfs = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('etfs.html', etfs=etfs, search_query=search_query)
    except Exception as e:
        return f"<h1>Error</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>"

@app.route('/etf/<etf_ticker>')
def etf_details(etf_ticker):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get ETF basic info
        cur.execute("""
            SELECT e.etf_ticker, e.etf_name, e.inception_date, e.aum, e.management_fee, 
                   e.number_of_stocks, f.fund_name, e.etf_review, e.annual_returns, e.comment_count
            FROM ETF e
            LEFT JOIN fund_has_etf fe ON e.etf_ticker = fe.etf_ticker
            LEFT JOIN fund_family f ON fe.fund_id = f.fund_id
            WHERE e.etf_ticker = %s
        """, (etf_ticker,))
        etf = cur.fetchone()
        
        # Get ETF categories
        cur.execute("""
            SELECT category_name
            FROM etf_category
            WHERE etf_ticker = %s
            ORDER BY category_name
        """, (etf_ticker,))
        categories = cur.fetchall()
        
        # Get sectors with weights
        cur.execute("""
            SELECT s.sector_name, es.sector_weight
            FROM ETF_has_Sector es
            JOIN Sector s ON es.sector_id = s.sector_id
            WHERE es.etf_ticker = %s
            ORDER BY es.sector_weight DESC
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
        
        # Get comments with usernames using the composite type
        cur.execute("""
            SELECT 
                c.comment_id,
                (c.comment).user_id,
                (c.comment).comment_text,
                (c.comment).comment_date,
                u.username
            FROM ETF_Comments c
            LEFT JOIN users u ON (c.comment).user_id = u.user_id::text
            WHERE c.etf_ticker = %s
            ORDER BY (c.comment).comment_date DESC
        """, (etf_ticker,))
        comments = cur.fetchall()
        
        # Check if user has liked this ETF
        is_liked = False
        if 'user_id' in session:
            cur.execute(
                "SELECT 1 FROM User_Likes_ETF WHERE user_id = %s AND etf_ticker = %s",
                (session['user_id'], etf_ticker)
            )
            is_liked = cur.fetchone() is not None
        
        cur.close()
        conn.close()
        
        # Format annual returns if they exist
        if etf and etf[8]:
            annual_returns = [float(r) for r in etf[8]]
        else:
            annual_returns = None
            
        return render_template('etf_details.html', 
                             etf=etf, 
                             categories=categories, 
                             sectors=sectors, 
                             stocks=stocks, 
                             is_liked=is_liked, 
                             comments=comments,
                             annual_returns=annual_returns)
    except Exception as e:
        return f"<h1>Error</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>"

@app.route('/etf/<etf_ticker>/comment', methods=['POST'])
@login_required
def add_comment(etf_ticker):
    try:
        comment_text = request.form.get('comment_text')
        if not comment_text:
            flash('Comment cannot be empty')
            return redirect(url_for('etf_details', etf_ticker=etf_ticker))
            
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Insert comment using the composite type
        cur.execute("""
            INSERT INTO ETF_Comments (etf_ticker, comment)
            VALUES (%s, ROW(%s, %s, CURRENT_TIMESTAMP)::comment_type)
        """, (etf_ticker, str(session['user_id']), comment_text))
        
        cur.close()
        conn.close()
        
        flash('Comment added successfully')
        return redirect(url_for('etf_details', etf_ticker=etf_ticker))
    except Exception as e:
        flash('Error adding comment')
        return redirect(url_for('etf_details', etf_ticker=etf_ticker))

@app.route('/stocks')
def list_stocks():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get search parameter if any
        search_query = request.args.get('q', '')
        
        if search_query:
            # If search query provided, filter results
            cur.execute("""
                SELECT s.stock_ticker, s.stock_name, s.ipo_date, s.stock_sector, sec.sector_name
                FROM Stock s
                LEFT JOIN Sector sec ON s.stock_sector = sec.sector_id
                WHERE s.stock_ticker ILIKE %s OR s.stock_name ILIKE %s
                ORDER BY s.stock_ticker
            """, ('%' + search_query + '%', '%' + search_query + '%'))
        else:
            # If no search query, return all
            cur.execute("""
                SELECT s.stock_ticker, s.stock_name, s.ipo_date, s.stock_sector, sec.sector_name
                FROM Stock s
                LEFT JOIN Sector sec ON s.stock_sector = sec.sector_id
                ORDER BY s.stock_ticker
            """)
            
        stocks = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('stocks.html', stocks=stocks, search_query=search_query)
    except Exception as e:
        return f"<h1>Error</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>"

@app.route('/stock/<stock_ticker>')
def stock_details(stock_ticker):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get stock basic info with sector name
        cur.execute("""
            SELECT s.*, sec.sector_name
            FROM Stock s
            LEFT JOIN Sector sec ON s.stock_sector = sec.sector_id
            WHERE s.stock_ticker = %s
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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        user_key = request.form['user_key']
        
        # Simple validation
        if not username or not user_key:
            flash('Username and password are required')
            return render_template('register.html')
            
        # Hash the password
        hashed_key = generate_password_hash(user_key)
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO Users (username, user_key) VALUES (%s, %s) RETURNING user_id",
                (username, hashed_key)
            )
            user_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            
            # Auto-login after registration
            session['user_id'] = user_id
            session['username'] = username
            
            flash('Registration successful! You are now logged in.')
            return redirect(url_for('my_etfs'))
        except Exception as e:
            flash(f'Error: {str(e)}')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        user_key = request.form['user_key']
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT user_id, user_key FROM Users WHERE username = %s", (username,))
            user = cur.fetchone()
            cur.close()
            conn.close()
            
            if user and check_password_hash(user[1], user_key):
                session['user_id'] = user[0]
                session['username'] = username
                flash('Login successful!')
                return redirect(url_for('my_etfs'))
            else:
                flash('Invalid username or password')
        except Exception as e:
            flash(f'Error: {str(e)}')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/my-etfs')
@login_required
def my_etfs():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT e.etf_ticker, e.etf_name, e.inception_date, e.aum, f.fund_name as fund_family
            FROM User_Likes_ETF ul
            JOIN ETF e ON ul.etf_ticker = e.etf_ticker
            JOIN Fund_has_ETF fe ON e.etf_ticker = fe.etf_ticker
            JOIN Fund_Family f ON fe.fund_id = f.fund_id
            WHERE ul.user_id = %s
            ORDER BY ul.liked_at DESC
        """, (session['user_id'],))
        liked_etfs = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('my_etfs.html', etfs=liked_etfs)
    except Exception as e:
        return f"<h1>Error</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>"

@app.route('/like-etf/<etf_ticker>', methods=['POST'])
@login_required
def like_etf(etf_ticker):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO User_Likes_ETF (user_id, etf_ticker) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (session['user_id'], etf_ticker)
        )
        conn.commit()
        cur.close()
        conn.close()
        flash(f'Added {etf_ticker} to your favorites!')
        return redirect(url_for('etf_details', etf_ticker=etf_ticker))
    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect(url_for('etf_details', etf_ticker=etf_ticker))

@app.route('/unlike-etf/<etf_ticker>', methods=['POST'])
@login_required
def unlike_etf(etf_ticker):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM User_Likes_ETF WHERE user_id = %s AND etf_ticker = %s",
            (session['user_id'], etf_ticker)
        )
        conn.commit()
        cur.close()
        conn.close()
        flash(f'Removed {etf_ticker} from your favorites')
        return redirect(url_for('etf_details', etf_ticker=etf_ticker))
    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect(url_for('etf_details', etf_ticker=etf_ticker))

@app.route('/sectors')
def list_sectors():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get search parameter if any
        search_query = request.args.get('q', '')
        
        if search_query:
            # If search query provided, filter results
            cur.execute("""
                SELECT sector_id, sector_name, annualized_return_1yr, annualized_return_3yr, annualized_return_5yr
                FROM Sector
                WHERE sector_id ILIKE %s OR sector_name ILIKE %s
                ORDER BY sector_name
            """, ('%' + search_query + '%', '%' + search_query + '%'))
        else:
            # If no search query, return all
            cur.execute("""
                SELECT sector_id, sector_name, annualized_return_1yr, annualized_return_3yr, annualized_return_5yr
                FROM Sector
                ORDER BY sector_name
            """)
            
        sectors = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('sectors.html', sectors=sectors, search_query=search_query)
    except Exception as e:
        return f"<h1>Error</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>"

@app.route('/sector/<sector_id>')
def sector_details(sector_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get sector basic info
        cur.execute("""
            SELECT *
            FROM Sector
            WHERE sector_id = %s
        """, (sector_id,))
        sector = cur.fetchone()
        
        # Get ETFs in this sector
        cur.execute("""
            SELECT e.etf_ticker, e.etf_name, es.sector_weight
            FROM ETF_has_Sector es
            JOIN ETF e ON es.etf_ticker = e.etf_ticker
            WHERE es.sector_id = %s
            ORDER BY es.sector_weight DESC
        """, (sector_id,))
        etfs = cur.fetchall()
        
        # Get stocks in this sector
        cur.execute("""
            SELECT stock_ticker, stock_name, ipo_date
            FROM Stock
            WHERE stock_sector = %s
            ORDER BY stock_ticker
        """, (sector_id,))
        stocks = cur.fetchall()
        
        cur.close()
        conn.close()
        return render_template('sector_details.html', sector=sector, etfs=etfs, stocks=stocks)
    except Exception as e:
        return f"<h1>Error</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>"

@app.route('/indexes')
def list_indexes():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get search parameter if any
        search_query = request.args.get('q', '')
        
        if search_query:
            # If search query provided, filter results
            cur.execute("""
                SELECT index_ticker, index_name, number_of_contributors, launch_date, base_value
                FROM market_index
                WHERE index_ticker ILIKE %s OR index_name ILIKE %s
                ORDER BY index_name
            """, ('%' + search_query + '%', '%' + search_query + '%'))
        else:
            # If no search query, return all
            cur.execute("""
                SELECT index_ticker, index_name, number_of_contributors, launch_date, base_value
                FROM market_index
                ORDER BY index_name
            """)
            
        indexes = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('indexes.html', indexes=indexes, search_query=search_query)
    except Exception as e:
        return f"<h1>Error</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>"

@app.route('/index/<index_ticker>')
def index_details(index_ticker):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get index basic info
        cur.execute("""
            SELECT *
            FROM market_index
            WHERE index_ticker = %s
        """, (index_ticker,))
        index = cur.fetchone()
        
        # Get ETFs tracking this index (assuming a table exists for this relationship)
        # Check if the etf_tracks_market_index table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'hg2736' AND table_name = 'etf_tracks_market_index'
            )
        """)
        table_exists = cur.fetchone()[0]
        
        etfs = []
        if table_exists:
            # If the table exists, get ETFs tracking this index
            cur.execute("""
                SELECT e.etf_ticker, e.etf_name
                FROM etf_tracks_market_index ei
                JOIN ETF e ON ei.etf_ticker = e.etf_ticker
                WHERE ei.index_ticker = %s
            """, (index_ticker,))
            etfs = cur.fetchall()
        
        # If the relationship table doesn't exist, try to get stocks in the index instead
        if not etfs:
            cur.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'hg2736' AND table_name = 'stock_in_index'
                )
            """)
            stock_table_exists = cur.fetchone()[0]
            
            if stock_table_exists:
                cur.execute("""
                    SELECT s.stock_ticker, s.stock_name, si.weight
                    FROM stock_in_index si
                    JOIN Stock s ON si.stock_ticker = s.stock_ticker
                    WHERE si.index_ticker = %s
                    ORDER BY si.weight DESC
                """, (index_ticker,))
                stocks_in_index = cur.fetchall()
                
                cur.close()
                conn.close()
                return render_template('index_details.html', index=index, etfs=etfs, stocks=stocks_in_index)
        
        cur.close()
        conn.close()
        return render_template('index_details.html', index=index, etfs=etfs)
    except Exception as e:
        return f"<h1>Error</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>"

@app.route('/recommendations')
@login_required
def etf_recommendations():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get ETFs the user has liked
        cur.execute("""
            SELECT etf_ticker 
            FROM User_Likes_ETF 
            WHERE user_id = %s
        """, (session['user_id'],))
        
        liked_etfs = [row[0] for row in cur.fetchall()]
        
        # If the user hasn't liked any ETFs yet, return an empty result
        if not liked_etfs:
            cur.close()
            conn.close()
            return render_template('recommendations.html', recommendations=[], liked_etfs=[])
        
        # Generate recommendations based on sector similarity
        # For each liked ETF, find other ETFs with similar sectors
        all_recommendations = []
        
        for etf_ticker in liked_etfs:
            cur.execute("""
                WITH user_etf_sectors AS (
                  -- Get the sectors for the ETF the user is interested in
                  SELECT sector_id
                  FROM ETF_has_Sector
                  WHERE etf_ticker = %s
                ),
                similar_etfs AS (
                  -- Find other ETFs that share these sectors
                  SELECT e.etf_ticker, e.etf_name, COUNT(*) AS common_sectors
                  FROM ETF e
                  JOIN ETF_has_Sector es ON e.etf_ticker = es.etf_ticker
                  WHERE es.sector_id IN (SELECT sector_id FROM user_etf_sectors)
                    AND e.etf_ticker <> %s
                    AND e.etf_ticker NOT IN %s
                  GROUP BY e.etf_ticker, e.etf_name
                )
                -- Get the top 5 ETFs based on the number of matching sectors
                SELECT etf_ticker, etf_name, common_sectors
                FROM similar_etfs
                ORDER BY common_sectors DESC
                LIMIT 5
            """, (etf_ticker, etf_ticker, tuple(liked_etfs) if liked_etfs else ('',)))
            
            recommendations = cur.fetchall()
            
            # Add the source ETF to each recommendation
            recommendations_with_source = [(etf_ticker, rec[0], rec[1], rec[2]) for rec in recommendations]
            all_recommendations.extend(recommendations_with_source)
        
        # Get ETF details for the liked ETFs to display
        liked_etfs_details = []
        if liked_etfs:
            placeholders = ','.join(['%s'] * len(liked_etfs))
            cur.execute(f"""
                SELECT etf_ticker, etf_name
                FROM ETF
                WHERE etf_ticker IN ({placeholders})
            """, tuple(liked_etfs))
            liked_etfs_details = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Sort the recommendations by the number of common sectors
        sorted_recommendations = sorted(all_recommendations, key=lambda x: x[3], reverse=True)
        
        # Limit to a unique set of top 10 recommendations
        unique_recommendations = []
        seen_etfs = set()
        for rec in sorted_recommendations:
            if rec[1] not in seen_etfs:
                seen_etfs.add(rec[1])
                unique_recommendations.append(rec)
                if len(unique_recommendations) >= 10:
                    break
        
        return render_template('recommendations.html', 
                              recommendations=unique_recommendations, 
                              liked_etfs=liked_etfs_details)
                              
    except Exception as e:
        return f"<h1>Error</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>"

# Add a route to get recommendations for a specific ETF
@app.route('/recommendations/<etf_ticker>')
def etf_specific_recommendations(etf_ticker):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get the ETF details
        cur.execute("""
            SELECT *
            FROM ETF
            WHERE etf_ticker = %s
        """, (etf_ticker,))
        source_etf = cur.fetchone()
        
        if not source_etf:
            return f"<h1>Error</h1><p>ETF with ticker {etf_ticker} not found</p>"
        
        # Generate recommendations based on sector similarity
        cur.execute("""
            WITH source_etf_sectors AS (
              -- Get the sectors for the source ETF
              SELECT sector_id
              FROM ETF_has_Sector
              WHERE etf_ticker = %s
            ),
            similar_etfs AS (
              -- Find other ETFs that share these sectors
              SELECT e.etf_ticker, e.etf_name, COUNT(*) AS common_sectors
              FROM ETF e
              JOIN ETF_has_Sector es ON e.etf_ticker = es.etf_ticker
              WHERE es.sector_id IN (SELECT sector_id FROM source_etf_sectors)
                AND e.etf_ticker <> %s
              GROUP BY e.etf_ticker, e.etf_name
            )
            -- Get the top ETFs based on the number of matching sectors
            SELECT etf_ticker, etf_name, common_sectors
            FROM similar_etfs
            ORDER BY common_sectors DESC
            LIMIT 5
        """, (etf_ticker, etf_ticker))
        
        recommendations = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template('specific_recommendations.html', 
                              recommendations=recommendations, 
                              source_etf=source_etf)
                              
    except Exception as e:
        return f"<h1>Error</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8111) 