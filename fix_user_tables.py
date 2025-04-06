#!/usr/bin/env python3
import psycopg2

# Connection details
host = '34.148.223.31'
port = '5432'
dbname = 'proj1part2'
user = 'hg2736'
password = '008096'
schema = 'hg2736'

# Connect to PostgreSQL
print("Connecting to PostgreSQL database...")
conn = psycopg2.connect(
    host=host, 
    port=port, 
    dbname=dbname, 
    user=user, 
    password=password
)
conn.autocommit = True  # Set autocommit mode

# Create a cursor
cur = conn.cursor()

# Set the schema
cur.execute(f"SET search_path TO {schema}")

# Drop existing tables
print("Dropping existing tables...")
cur.execute("DROP TABLE IF EXISTS User_Likes_ETF")
cur.execute("DROP TABLE IF EXISTS Users")
print("Tables dropped.")

# Create Users table
print("Creating Users table...")
cur.execute("""
CREATE TABLE Users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    user_key VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Create User_Likes_ETF table
print("Creating User_Likes_ETF table...")
cur.execute("""
CREATE TABLE User_Likes_ETF (
    user_id INTEGER REFERENCES Users(user_id),
    etf_ticker VARCHAR REFERENCES ETF(etf_ticker),
    liked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, etf_ticker)
)
""")

# Close connection
cur.close()
conn.close()
print("✅ User tables created successfully! Database connection closed.")

print("You can now run 'python app.py' and register with your username and password.") 