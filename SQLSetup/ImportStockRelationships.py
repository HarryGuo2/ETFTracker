#!/usr/bin/env python3
"""
Script to import ETF stock relationship data (Stock_in_ETF and Stock_in_Index)
"""

import pandas as pd
import psycopg2
import sys
import os

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
    
    # Get valid ETF tickers
    cursor.execute(f"SELECT etf_ticker FROM {schema}.etf")
    valid_etfs = {row[0] for row in cursor.fetchall()}
    print(f"Valid ETF tickers in database: {valid_etfs}")
    
    # Get valid stock tickers
    cursor.execute(f"SELECT stock_ticker FROM {schema}.stock")
    valid_stocks = {row[0] for row in cursor.fetchall()}
    print(f"Found {len(valid_stocks)} valid stocks in database")
    
    # Get valid index tickers
    cursor.execute(f"SELECT index_ticker FROM {schema}.market_index")
    valid_indices = {row[0] for row in cursor.fetchall()}
    print(f"Valid index tickers in database: {valid_indices}")
    
    # 1. Import Stock_in_ETF
    print("\nImporting Stock_in_ETF...")
    
    df_stock_etf = excel_data["Stock_in_ETF"]
    
    # Insert data
    se_inserted = 0
    se_errors = 0
    
    for _, row in df_stock_etf.iterrows():
        etf_ticker = row["etf_ticker"]
        stock_ticker = row["stock_ticker"]
        stock_weight = float(row["stock_weight"]) if pd.notna(row["stock_weight"]) else None
        
        # Skip if ETF or stock doesn't exist
        if etf_ticker not in valid_etfs:
            if se_errors < 3:
                print(f"  Skipping stock {stock_ticker} for ETF {etf_ticker} - ETF not in database")
            se_errors += 1
            continue
            
        if stock_ticker not in valid_stocks:
            if se_errors < 3:
                print(f"  Skipping stock {stock_ticker} for ETF {etf_ticker} - Stock not in database")
            se_errors += 1
            continue
        
        try:
            # Check if this relationship already exists
            cursor.execute(f"""
            SELECT 1 FROM {schema}.stock_in_etf
            WHERE etf_ticker = %s AND stock_ticker = %s
            """, (etf_ticker, stock_ticker))
            
            exists = cursor.fetchone()
            
            if exists:
                print(f"  Stock {stock_ticker} in ETF {etf_ticker} already exists - skipping")
                continue
            
            # Insert
            query = f"""
            INSERT INTO {schema}.stock_in_etf (etf_ticker, stock_ticker, stock_weight)
            VALUES (%s, %s, %s);
            """
            cursor.execute(query, (etf_ticker, stock_ticker, stock_weight))
            se_inserted += 1
            
            # Commit after each successful insert
            conn.commit()
            
            if se_inserted % 10 == 0:
                print(f"  Progress: {se_inserted} stock-ETF relationships inserted")
        
        except Exception as e:
            conn.rollback()
            se_errors += 1
            if se_errors <= 3:
                print(f"  Error inserting stock {stock_ticker} for ETF {etf_ticker}: {e}")
            elif se_errors == 4:
                print("  Additional errors omitted...")
    
    print(f"  Finished: {se_inserted} stock-ETF relationships inserted, {se_errors} errors")
    
    # 2. Import Stock_in_Index
    print("\nImporting Stock_in_Index...")
    
    df_stock_idx = excel_data["Stock_in_Index"]
    
    # Insert data
    si_inserted = 0
    si_errors = 0
    
    for _, row in df_stock_idx.iterrows():
        stock_ticker = row["stock_ticker"]
        index_ticker = row["index_ticker"]
        weight = float(row["weight"]) if pd.notna(row["weight"]) else None
        
        # Skip if stock or index doesn't exist
        if stock_ticker not in valid_stocks:
            if si_errors < 3:
                print(f"  Skipping stock {stock_ticker} for index {index_ticker} - Stock not in database")
            si_errors += 1
            continue
            
        if index_ticker not in valid_indices:
            if si_errors < 3:
                print(f"  Skipping stock {stock_ticker} for index {index_ticker} - Index not in database")
            si_errors += 1
            continue
        
        try:
            # Check if this relationship already exists
            cursor.execute(f"""
            SELECT 1 FROM {schema}.stock_in_index
            WHERE stock_ticker = %s AND index_ticker = %s
            """, (stock_ticker, index_ticker))
            
            exists = cursor.fetchone()
            
            if exists:
                print(f"  Stock {stock_ticker} in index {index_ticker} already exists - skipping")
                continue
            
            # Insert
            query = f"""
            INSERT INTO {schema}.stock_in_index (stock_ticker, index_ticker, weight)
            VALUES (%s, %s, %s);
            """
            cursor.execute(query, (stock_ticker, index_ticker, weight))
            si_inserted += 1
            
            # Commit after each successful insert
            conn.commit()
            
            if si_inserted % 10 == 0:
                print(f"  Progress: {si_inserted} stock-index relationships inserted")
        
        except Exception as e:
            conn.rollback()
            si_errors += 1
            if si_errors <= 3:
                print(f"  Error inserting stock {stock_ticker} for index {index_ticker}: {e}")
            elif si_errors == 4:
                print("  Additional errors omitted...")
    
    print(f"  Finished: {si_inserted} stock-index relationships inserted, {si_errors} errors")
    
    # Close connection
    cursor.close()
    conn.close()
    
    print("\nStock relationship import completed.")

if __name__ == "__main__":
    main() 