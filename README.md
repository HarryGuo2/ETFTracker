# ETF Tracker

A web application for tracking and analyzing ETFs (Exchange Traded Funds) and their underlying stocks.

> We want to make it easy for users to invest in ETFs.

## Features

- User authentication system with login and registration
- Personalized ETF watchlist ("My Favorite ETFs")
- Browse and search ETFs, stocks, sectors, and market indexes
- View detailed information about each ETF including:
  - Fund family information
  - Sector allocations
  - Top stock holdings with weights
- View detailed information about each stock including ETFs that hold it
- View sector performance metrics and associated ETFs
- View market indexes and their tracking ETFs
- Search functionality on all listing pages

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: PostgreSQL
- **Frontend**: HTML, CSS, Bootstrap (rendered with Flask templates)

## Database Schema

The application uses the following database tables:
- `ETF`: Information about ETFs (ticker, name, inception date, etc.)
- `Stock`: Information about individual stocks
- `Fund_Family`: Information about fund providers
- `Fund_has_ETF`: Relationship between fund families and ETFs
- `Sector`: Market sectors information
- `ETF_has_Sector`: ETF allocations by sector
- `Stock_in_ETF`: Stock holdings in each ETF with weights
- `Index_Table`: Market indexes information
- `ETF_tracks_Index`: Relationship between ETFs and the indexes they track
- `Users`: User authentication information
- `User_Likes_ETF`: Tracks which ETFs a user has added to their favorites

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/HarryGuo2/ETFTracker.git
   cd ETFTracker
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file in the project root with your database credentials

4. Create the user database tables:
   ```
   python fix_user_tables.py
   ```

5. Run the application:
   ```
   python app.py
   ```

6. Access the application at `http://localhost:8111`

## User Flow

1. Register for an account or login
2. Browse the available ETFs, stocks, sectors, or indexes
3. Use the search functionality to find specific items
4. View detailed information about ETFs that interest you
5. Add ETFs to your favorites by clicking the "Add to Favorites" button
6. Access your personalized ETF watchlist from "My Favorite ETFs" in the navigation

## Screenshots

*[Add screenshots here]*

## Future Enhancements

- User authentication and personalized watchlists
- Historical performance tracking
- Visualization of ETF compositions
- Comparison tools between multiple ETFs
