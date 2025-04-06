#!/usr/bin/env python3
"""
Script to generate and insert random user data into User and User_interest_ETF tables
"""

import psycopg2
import random
import string
import sys

def generate_random_string(length):
    """Generate a random string of fixed length"""
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

def main():
    # Connection details
    host = "34.148.223.31"
    port = "5432"
    dbname = "proj1part2"
    user = "hg2736"
    password = "008096"
    schema = "hg2736"
    
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
    
    # Get existing ETF tickers to use for user interests
    try:
        cursor.execute(f"SELECT etf_ticker FROM {schema}.etf")
        etf_tickers = [row[0] for row in cursor.fetchall()]
        
        if not etf_tickers:
            print("No ETF tickers found in the database. Make sure ETF data is imported first.")
            cursor.close()
            conn.close()
            sys.exit(1)
            
        print(f"Found {len(etf_tickers)} ETF tickers")
    except Exception as e:
        print(f"Error retrieving ETF tickers: {e}")
        cursor.close()
        conn.close()
        sys.exit(1)
    
    # Generate 10 random users
    print("\nGenerating 10 random users...")
    
    user_ids = []
    for i in range(1, 11):
        user_id = f"U{i:03d}"
        user_name = f"user{i}"
        user_password = generate_random_string(10)
        
        try:
            # Insert user
            query = f"""
            INSERT INTO {schema}."User" (user_id, user_name, user_password)
            VALUES (%s, %s, %s);
            """
            cursor.execute(query, (user_id, user_name, user_password))
            user_ids.append(user_id)
            print(f"  Inserted User: {user_id} ({user_name})")
        except Exception as e:
            conn.rollback()
            print(f"  Error inserting User {user_id}: {e}")
    
    # Commit user inserts
    conn.commit()
    
    # Generate user interests
    print("\nGenerating user interests...")
    
    interest_count = 0
    for user_id in user_ids:
        # Each user will be interested in 1-5 random ETFs
        num_interests = random.randint(1, min(5, len(etf_tickers)))
        
        # Select random ETFs
        user_etfs = random.sample(etf_tickers, num_interests)
        
        for etf_ticker in user_etfs:
            try:
                # Insert user interest
                query = f"""
                INSERT INTO {schema}.user_interest_etf (user_id, etf_ticker)
                VALUES (%s, %s);
                """
                cursor.execute(query, (user_id, etf_ticker))
                interest_count += 1
                print(f"  User {user_id} interested in ETF {etf_ticker}")
            except Exception as e:
                conn.rollback()
                print(f"  Error inserting interest for User {user_id} in ETF {etf_ticker}: {e}")
    
    # Commit interest inserts
    conn.commit()
    
    print(f"\nInserted {len(user_ids)} users and {interest_count} user interests")
    
    # Close connection
    cursor.close()
    conn.close()
    
    print("\nUser data insertion completed.")

if __name__ == "__main__":
    main() 