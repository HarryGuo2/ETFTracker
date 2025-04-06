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
conn = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password)
cursor = conn.cursor()

# Get list of tables
cursor.execute(f"""
SELECT table_name
FROM information_schema.tables
WHERE table_schema = '{schema}' AND table_type = 'BASE TABLE'
ORDER BY table_name
""")

tables = [row[0] for row in cursor.fetchall()]

# Count records in each table
print(f'Records in {schema} schema:')
print('----------------------')
for table in tables:
    try:
        # Handle "User" table specially (quoted identifier)
        if table.lower() == 'user':
            cursor.execute(f'SELECT COUNT(*) FROM {schema}."User"')
        else:
            cursor.execute(f'SELECT COUNT(*) FROM {schema}.{table}')
        count = cursor.fetchone()[0]
        print(f'{table}: {count}')
    except Exception as e:
        print(f'{table}: Error - {e}')

# Close connection
cursor.close()
conn.close() 