#!/usr/bin/env python3
"""
Script to fix ETF data import issues by truncating long values and handling duplicates
"""

import pandas as pd
import psycopg2
import sys
import os
from datetime import datetime

def truncate_if_needed(value, max_length=30):
    """Truncate string values if they exceed max_length"""
    if isinstance(value, str) and len(value) > max_length:
        return value[:max_length]
    return value

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
    
    # 1. Fix ETF table - Focus on this first as many other tables depend on it
    print("\nFixing ETF table...")
    
    df_etf = excel_data["ETF"]
    
    # Display the actual column names in the Excel
    print(f"ETF Excel columns: {list(df_etf.columns)}")
    
    # Clean up and prepare data
    etf_data = []
    for _, row in df_etf.iterrows():
        etf_ticker = row["ETF Ticker"]
        etf_name = truncate_if_needed(row["ETF Name"], 30)
        inception_date = row["Inception Date"].date().isoformat() if pd.notna(row["Inception Date"]) else None
        
        # Convert management fee to numeric
        management_fee = None
        if "Management Fee(%）" in row and pd.notna(row["Management Fee(%）"]):
            management_fee = float(row["Management Fee(%）"])
        
        # Convert AUM to numeric
        aum = None
        if "Net Assets" in row and pd.notna(row["Net Assets"]):
            aum = float(row["Net Assets"])
        
        # Convert number of stocks to integer
        num_stocks = None
        if "Number of Stocks" in row and pd.notna(row["Number of Stocks"]):
            num_stocks = int(row["Number of Stocks"])
        
        etf_data.append((etf_ticker, etf_name, inception_date, aum, management_fee, num_stocks))
    
    # Insert ETF data
    for etf in etf_data:
        try:
            # Check if this ETF already exists
            cursor.execute(f"SELECT 1 FROM {schema}.etf WHERE etf_ticker = %s", (etf[0],))
            exists = cursor.fetchone()
            
            if exists:
                print(f"  ETF {etf[0]} already exists - skipping")
                continue
            
            # Insert the ETF
            query = f"""
            INSERT INTO {schema}.etf (etf_ticker, etf_name, inception_date, aum, management_fee, number_of_stocks)
            VALUES (%s, %s, %s, %s, %s, %s);
            """
            cursor.execute(query, etf)
            print(f"  Inserted ETF: {etf[0]}")
        except Exception as e:
            conn.rollback()
            print(f"  Error inserting ETF {etf[0]}: {e}")
    
    conn.commit()
    
    # 2. Fix Fund_Family table
    print("\nFixing Fund_Family table...")
    
    df_fund = excel_data["Fund_Family"]
    
    # Display the actual column names in the Excel
    print(f"Fund_Family Excel columns: {list(df_fund.columns)}")
    
    # Clean up and prepare data
    fund_data = []
    for _, row in df_fund.iterrows():
        fund_id = row["fund_family_id"]
        fund_name = truncate_if_needed(row["fund_name"], 30)
        headquarters = truncate_if_needed(row["headquater"], 30) if pd.notna(row["headquater"]) else None
        
        # Convert number of funds to integer
        num_funds = None
        if "ETF_n" in row and pd.notna(row["ETF_n"]):
            num_funds = int(row["ETF_n"])
        
        # Convert AUM to numeric
        aum = None
        if "fund_aum(B)" in row and pd.notna(row["fund_aum(B)"]):
            aum = float(row["fund_aum(B)"])
        
        fund_data.append((fund_id, fund_name, headquarters, aum, num_funds))
    
    # Insert Fund_Family data
    for fund in fund_data:
        try:
            # Check if this fund already exists
            cursor.execute(f"SELECT 1 FROM {schema}.fund_family WHERE fund_id = %s", (fund[0],))
            exists = cursor.fetchone()
            
            if exists:
                print(f"  Fund {fund[0]} already exists - skipping")
                continue
            
            # Insert the fund
            query = f"""
            INSERT INTO {schema}.fund_family (fund_id, fund_name, headquarters, aum, number_of_funds)
            VALUES (%s, %s, %s, %s, %s);
            """
            cursor.execute(query, fund)
            print(f"  Inserted Fund: {fund[0]}")
        except Exception as e:
            conn.rollback()
            print(f"  Error inserting Fund {fund[0]}: {e}")
    
    conn.commit()
    
    # 3. Fix Sector table
    print("\nFixing Sector table...")
    
    df_sector = excel_data["Sector"]
    
    # Display the actual column names in the Excel
    print(f"Sector Excel columns: {list(df_sector.columns)}")
    
    # Clean up and prepare data
    sector_data = []
    for _, row in df_sector.iterrows():
        sector_id = row["Sector_id"]
        sector_name = truncate_if_needed(row["Sector"], 30)
        
        # Convert returns to numeric
        return_1yr = float(row["1-Year Return"]) if pd.notna(row["1-Year Return"]) else None
        return_3yr = float(row["3-Year Return"]) if pd.notna(row["3-Year Return"]) else None
        return_5yr = float(row["5-Year Return"]) if pd.notna(row["5-Year Return"]) else None
        
        sector_data.append((sector_id, sector_name, return_1yr, return_3yr, return_5yr))
    
    # Insert Sector data
    for sector in sector_data:
        try:
            # Check if this sector already exists
            cursor.execute(f"SELECT 1 FROM {schema}.sector WHERE sector_id = %s", (sector[0],))
            exists = cursor.fetchone()
            
            if exists:
                print(f"  Sector {sector[0]} already exists - skipping")
                continue
            
            # Insert the sector
            query = f"""
            INSERT INTO {schema}.sector (sector_id, sector_name, annualized_return_1yr, annualized_return_3yr, annualized_return_5yr)
            VALUES (%s, %s, %s, %s, %s);
            """
            cursor.execute(query, sector)
            print(f"  Inserted Sector: {sector[0]} - {sector[1]}")
        except Exception as e:
            conn.rollback()
            print(f"  Error inserting Sector {sector[0]}: {e}")
    
    conn.commit()
    
    # Close connection
    cursor.close()
    conn.close()
    
    print("\nFix script completed. Please check the database for changes.")

if __name__ == "__main__":
    main() 