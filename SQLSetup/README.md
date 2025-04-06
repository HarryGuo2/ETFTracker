# ETF Tracker Database Project

This project implements a PostgreSQL database for tracking ETFs (Exchange-Traded Funds), their components, and user interests.

## Database Structure

The database contains the following main tables:
- `User`: Stores user information
- `ETF`: Contains ETF details
- `Sector`: Defines market sectors
- `Stock`: Contains individual stock information
- `Market_Index`: Tracks market indices
- `Fund_Family`: Groups ETFs by fund family
- `ETF_Category`: Categorizes ETFs
- `ETF_has_Sector`: Links ETFs to sectors
- `Fund_has_ETF`: Links fund families to ETFs
- `Stock_in_ETF`: Maps stocks to ETFs
- `Stock_in_Index`: Maps stocks to market indices
- `User_interest_ETF`: Tracks user ETF preferences

## Key Files

1. **Data Import Scripts**:
   - `FixImport.py`: Imports base tables (ETF, Fund_Family, Sector)
   - `ImportRelationships.py`: Imports relationship data
   - `ImportStockRelationships.py`: Handles stock relationships
   - `InsertUserData.py`: Generates and inserts random user data

2. **Utility Scripts**:
   - `CountRecords.py`: Counts records in each table

3. **Analysis Queries**:
   - `InterestingQueries.sql`: Contains three insightful queries:
     1. Most Popular ETFs Among Users
     2. Stock Overlap Analysis Between ETFs
     3. User Investment Profile Analysis

## Database Connection Details

- Host: 34.148.223.31
- Port: 5432
- Database: proj1part2
- User: hg2736
- Schema: hg2736

## Key Features

1. **Data Import**:
   - Handles data type conversions
   - Manages foreign key constraints
   - Truncates overly long strings
   - Checks for duplicates

2. **User Management**:
   - Generates random user data
   - Assigns ETF interests
   - Tracks user preferences

3. **Analysis Capabilities**:
   - ETF popularity analysis
   - Stock overlap detection
   - User investment profile analysis

## Usage

1. Import base data:
   ```bash
   python FixImport.py
   ```

2. Import relationships:
   ```bash
   python ImportRelationships.py
   python ImportStockRelationships.py
   ```

3. Generate user data:
   ```bash
   python InsertUserData.py
   ```

4. Check record counts:
   ```bash
   python CountRecords.py
   ```

5. Run analysis queries:
   ```bash
   psql -h 34.148.223.31 -p 5432 -d proj1part2 -U hg2736 -f InterestingQueries.sql
   ``` 