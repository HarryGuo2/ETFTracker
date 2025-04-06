#!/usr/bin/env python3
"""
Script to import ETF relationship data after the base tables have been populated
"""

import pandas as pd
import psycopg2
import sys
import os
from datetime import datetime

def main():
    # Connection details
    host = "34.148.223.31"
    port = "5432"
    dbname = "proj1part2"
    user = "hg2736"
    password = "008096"
    schema = "hg2736"
    
    # Excel file path
    excel_file = "ETFTrackerDatabase.xlsx"
    
    print(f"Reading {excel_file}...")
    
    # Read Excel file
    try:
        excel_data = pd.read_excel(excel_file, sheet_name=None)
        print(f"Found {len(excel_data)} sheets: {', '.join(excel_data.keys())}")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        sys.exit(1)
    
    # Connect to PostgreSQL
    print(f"Connecting to PostgreSQL at {host}:{port}, database {dbname}, user {user}...")
    
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )
        conn.autocommit = False
        print("Connected successfully.")
    except Exception as e:
        print(f"Connection error: {e}")
        sys.exit(1)
    
    cursor = conn.cursor()
    
    # 1. First finish fixing Stock table
    print("\nFixing Stock table...")
    
    df_stock = excel_data["Stock"]
    
    # Get a list of valid sector_ids from the database
    cursor.execute(f"SELECT sector_id FROM {schema}.sector")
    valid_sectors = {row[0] for row in cursor.fetchall()}
    print(f"Valid sector IDs in database: {valid_sectors}")
    
    # Clean up and prepare data
    stock_data = []
    for _, row in df_stock.iterrows():
        stock_ticker = row["stock_ticker"]
        stock_name = row["stock_name"]
        if len(stock_name) > 30:
            stock_name = stock_name[:30]
            
        # Handle date properly - could be a string or Timestamp
        ipo_date = None
        if pd.notna(row["IPO_date"]):
            if isinstance(row["IPO_date"], pd.Timestamp):
                ipo_date = row["IPO_date"].date().isoformat()
            elif isinstance(row["IPO_date"], str):
                # Try to parse from string - might be in different formats
                try:
                    # First try to parse as date
                    ipo_date = pd.to_datetime(row["IPO_date"]).date().isoformat()
                except:
                    # Just use the string directly
                    ipo_date = row["IPO_date"]
            else:
                ipo_date = str(row["IPO_date"])
        
        # Only use sector_id if it's valid in the database
        sector_id = row["sector_id"] if pd.notna(row["sector_id"]) and row["sector_id"] in valid_sectors else None
        
        stock_data.append((stock_ticker, stock_name, ipo_date, sector_id))
    
    # Insert Stock data
    for stock in stock_data:
        try:
            # Check if this stock already exists
            cursor.execute(f"SELECT 1 FROM {schema}.stock WHERE stock_ticker = %s", (stock[0],))
            exists = cursor.fetchone()
            
            if exists:
                print(f"  Stock {stock[0]} already exists - skipping")
                continue
            
            # Insert the stock
            query = f"""
            INSERT INTO {schema}.stock (stock_ticker, stock_name, ipo_date, stock_sector)
            VALUES (%s, %s, %s, %s);
            """
            cursor.execute(query, stock)
            print(f"  Inserted Stock: {stock[0]}")
        except Exception as e:
            conn.rollback()
            print(f"  Error inserting Stock {stock[0]}: {e}")
    
    conn.commit()
    
    # 2. Import ETF_Category
    print("\nImporting ETF_Category...")
    
    df_cat = excel_data["ETF_Category"]
    
    # Get valid ETF tickers
    cursor.execute(f"SELECT etf_ticker FROM {schema}.etf")
    valid_etfs = {row[0] for row in cursor.fetchall()}
    print(f"Valid ETF tickers in database: {valid_etfs}")
    
    # Insert data
    cat_inserted = 0
    cat_errors = 0
    
    for _, row in df_cat.iterrows():
        etf_ticker = row["etf_ticker"]
        category_id = row["category_id"]
        category_name = row["category_name"]
        
        if len(category_name) > 30:
            category_name = category_name[:30]
        
        # Skip if ETF doesn't exist
        if etf_ticker not in valid_etfs:
            print(f"  Skipping category for ETF {etf_ticker} - ETF not in database")
            continue
        
        try:
            # Check if this category already exists
            cursor.execute(f"""
            SELECT 1 FROM {schema}.etf_category
            WHERE etf_ticker = %s AND category_id = %s
            """, (etf_ticker, category_id))
            
            exists = cursor.fetchone()
            
            if exists:
                print(f"  Category for ETF {etf_ticker} already exists - skipping")
                continue
            
            # Insert
            query = f"""
            INSERT INTO {schema}.etf_category (etf_ticker, category_id, category_name)
            VALUES (%s, %s, %s);
            """
            cursor.execute(query, (etf_ticker, category_id, category_name))
            cat_inserted += 1
            
            # Commit after each successful insert
            conn.commit()
            
            if cat_inserted % 10 == 0:
                print(f"  Progress: {cat_inserted} categories inserted")
        
        except Exception as e:
            conn.rollback()
            cat_errors += 1
            if cat_errors <= 3:
                print(f"  Error inserting category for ETF {etf_ticker}: {e}")
            elif cat_errors == 4:
                print("  Additional errors omitted...")
    
    print(f"  Finished: {cat_inserted} categories inserted, {cat_errors} errors")
    
    # 3. Import ETF_has_Sector
    print("\nImporting ETF_has_Sector...")
    
    df_etf_sector = excel_data["ETF_has_Sector"]
    
    # Insert data
    es_inserted = 0
    es_errors = 0
    
    for _, row in df_etf_sector.iterrows():
        etf_ticker = row["etf_ticker"]
        sector_id = row["sector_id"]
        sector_weight = float(row["sector_weight"]) if pd.notna(row["sector_weight"]) else None
        
        # Skip if ETF or sector doesn't exist
        if etf_ticker not in valid_etfs:
            if es_errors < 3:
                print(f"  Skipping sector assignment for ETF {etf_ticker} - ETF not in database")
            continue
            
        if sector_id not in valid_sectors:
            if es_errors < 3:
                print(f"  Skipping sector {sector_id} for ETF {etf_ticker} - Sector not in database")
            continue
        
        try:
            # Check if this relationship already exists
            cursor.execute(f"""
            SELECT 1 FROM {schema}.etf_has_sector
            WHERE etf_ticker = %s AND sector_id = %s
            """, (etf_ticker, sector_id))
            
            exists = cursor.fetchone()
            
            if exists:
                print(f"  Sector {sector_id} for ETF {etf_ticker} already exists - skipping")
                continue
            
            # Insert
            query = f"""
            INSERT INTO {schema}.etf_has_sector (etf_ticker, sector_id, sector_weight)
            VALUES (%s, %s, %s);
            """
            cursor.execute(query, (etf_ticker, sector_id, sector_weight))
            es_inserted += 1
            
            # Commit after each successful insert
            conn.commit()
            
            if es_inserted % 10 == 0:
                print(f"  Progress: {es_inserted} sector assignments inserted")
        
        except Exception as e:
            conn.rollback()
            es_errors += 1
            if es_errors <= 3:
                print(f"  Error inserting sector {sector_id} for ETF {etf_ticker}: {e}")
            elif es_errors == 4:
                print("  Additional errors omitted...")
    
    print(f"  Finished: {es_inserted} sector assignments inserted, {es_errors} errors")
    
    # 4. Import Fund_has_ETF
    print("\nImporting Fund_has_ETF...")
    
    df_fund_etf = excel_data["Fund_has_ETF"]
    
    # Get valid fund IDs
    cursor.execute(f"SELECT fund_id FROM {schema}.fund_family")
    valid_funds = {row[0] for row in cursor.fetchall()}
    print(f"Valid fund IDs in database: {valid_funds}")
    
    # Insert data
    fe_inserted = 0
    fe_errors = 0
    
    for _, row in df_fund_etf.iterrows():
        etf_ticker = row["etf_ticker"]
        fund_id = row["fund_family_id"]
        
        # Skip if ETF or fund doesn't exist
        if etf_ticker not in valid_etfs:
            if fe_errors < 3:
                print(f"  Skipping fund assignment for ETF {etf_ticker} - ETF not in database")
            continue
            
        if fund_id not in valid_funds:
            if fe_errors < 3:
                print(f"  Skipping fund {fund_id} for ETF {etf_ticker} - Fund not in database")
            continue
        
        try:
            # Check if this relationship already exists
            cursor.execute(f"""
            SELECT 1 FROM {schema}.fund_has_etf
            WHERE etf_ticker = %s
            """, (etf_ticker,))
            
            exists = cursor.fetchone()
            
            if exists:
                print(f"  Fund assignment for ETF {etf_ticker} already exists - skipping")
                continue
            
            # Insert
            query = f"""
            INSERT INTO {schema}.fund_has_etf (etf_ticker, fund_id)
            VALUES (%s, %s);
            """
            cursor.execute(query, (etf_ticker, fund_id))
            fe_inserted += 1
            
            # Commit after each successful insert
            conn.commit()
            
            if fe_inserted % 10 == 0:
                print(f"  Progress: {fe_inserted} fund assignments inserted")
        
        except Exception as e:
            conn.rollback()
            fe_errors += 1
            if fe_errors <= 3:
                print(f"  Error inserting fund {fund_id} for ETF {etf_ticker}: {e}")
            elif fe_errors == 4:
                print("  Additional errors omitted...")
    
    print(f"  Finished: {fe_inserted} fund assignments inserted, {fe_errors} errors")
    
    # Close connection
    cursor.close()
    conn.close()
    
    print("\nRelationship import completed.")

if __name__ == "__main__":
    main() 