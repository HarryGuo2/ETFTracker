# ETF Tracker

A web application for tracking and analyzing ETFs (Exchange Traded Funds) and their underlying stocks.

## Features

- Browse a list of ETFs with their details (ticker, name, inception date, AUM)
- View detailed information about each ETF including:
  - Fund family information
  - Sector allocations
  - Top stock holdings with weights
- Browse a list of stocks
- View detailed information about each stock including ETFs that hold it

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

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ETFTracker.git
   cd ETFTracker
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file in the project root with your database credentials

4. Run the application:
   ```
   python app.py
   ```

5. Access the application at `http://localhost:8111`

## Screenshots

*[Add screenshots here]*

## Future Enhancements

- User authentication and personalized watchlists
- Historical performance tracking
- Visualization of ETF compositions
- Comparison tools between multiple ETFs 