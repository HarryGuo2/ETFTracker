# ETF Tracker Application - Project Part 3 Submission

## Database Information
- **PostgreSQL Account:** hg2736
- **Server:** 34.148.223.31:5432
- **Database Name:** proj1part2
- **Schema:** hg2736

This is the same database that was used for Part 2.

## Application URL
The ETF Tracker application is deployed and available at:
- **URL:** http://34.23.64.195:8111/

The virtual machine will remain running throughout the evaluation period to ensure the URL remains accessible.

## Deployment Details
The application is deployed on Google Cloud Platform using the following setup:

### Running with Screen
To ensure the application runs continuously even after SSH disconnection, we use the `screen` utility:

```bash
# Install screen (if not already installed)
sudo apt-get install screen

# Start a new screen session
screen

# Navigate to application directory
cd ~/etf-tracker/ETFTracker

# Activate virtual environment
source ~/etf-tracker/venv/bin/activate

# Run the Flask application
python3 app.py

# Detach from screen (Ctrl+A, then D)
# This keeps the application running in the background
```

To reconnect to the running application:
```bash
screen -r
```

### Database Connection
The application connects to the PostgreSQL database with the following configuration:
```python
DB_HOST = "34.148.223.31"
DB_PORT = "5432"
DB_NAME = "proj1part2"
DB_USER = "hg2736"
DB_SCHEMA = "hg2736"
```

## Implementation of Original Proposal

### Features Implemented (as proposed in Part 1)
1. **Core Data Browsing and Visualization:**
   - Browse ETFs, stocks, sectors, and market indices
   - View detailed information about each entity
   - Explore relationships between entities (e.g., ETFs holding specific stocks)
   - Search functionality for all entity types

2. **User Authentication System:**
   - User registration and login
   - Password hashing for security
   - Session management

3. **Personalization Features:**
   - Add/remove ETFs to/from user favorites
   - View list of favorite ETFs with detailed information
   - Personalized dashboard for logged-in users

4. **ETF Recommendation System:**
   - Sector-based similarity algorithm
   - Personalized recommendations based on user's liked ETFs
   - Single ETF similarity recommendations
   - Visualization of similarity scores

### Additional Features (not in original proposal)
1. **Enhanced UI/UX:**
   - Modern Bootstrap-based responsive design
   - Improved navigation and user flow
   - Mobile-friendly layout
   - Icons and visual cues for better user experience

2. **ETF Categories:**
   - Added ETF category information
   - Visual display of categories as badges
   - Improved data representation

3. **Data Formatting and Display:**
   - Better date formatting
   - Currency formatting with appropriate suffixes (B, M)
   - Handling of null values throughout the application
   - Progress bars for visualizing weights and similarities

4. **Cloud Deployment:**
   - Deployed on Google Cloud Platform
   - Configured for continuous operation

### Features Not Implemented
All features from the original proposal were successfully implemented. The only minor modification was to focus the recommendation system on sector-based similarity rather than implementing multiple recommendation algorithms, as this proved to be the most relevant approach for ETF comparisons.

## Most Interesting Database Operations

### 1. ETF Recommendation Page
**URL:** http://34.23.64.195:8111/recommendations

This page generates personalized ETF recommendations based on the ETFs a user has liked. It involves complex database operations:

- **Database Operations:** 
  - Retrieves all ETFs liked by the current user
  - For each liked ETF, identifies its sectors
  - Finds other ETFs that share these sectors
  - Counts the number of common sectors between ETFs
  - Ranks ETFs by similarity score
  - Deduplicates recommendations across multiple source ETFs
  - Returns a unique set of top recommendations

- **Why It's Interesting:**
  This operation involves multiple joins, aggregations, and a sophisticated ranking algorithm. It demonstrates how to leverage existing data relationships (ETF-sector) to create value-added features without requiring additional data collection. The query uses Common Table Expressions (CTEs) to break down the complex logic into manageable components, making it both performant and maintainable.

### 2. Stock Details Page
**URL:** http://34.23.64.195:8111/stock/AAPL (example)

This page shows comprehensive information about a stock and its relationships within the investment ecosystem:

- **Database Operations:**
  - Retrieves basic stock information with a join to the Sector table to get sector names
  - Finds all ETFs that hold the stock along with the weight of the stock in each ETF
  - Combines data from multiple tables (Stock, Sector, Stock_in_ETF, ETF)
  - Orders results by stock weight to show the ETFs where this stock has the most impact

- **Why It's Interesting:**
  This page demonstrates how relational databases excel at showing interconnections between entities. With just a few joins, we can show investors not only information about a stock but also how it's represented across various ETFs. This helps users understand both direct investment options (the stock itself) and indirect options (ETFs containing the stock at various weights). The ordering by weight provides additional analytical value by highlighting where the stock has the most significant presence.

Both these operations showcase how well-designed database schemas can support complex analytical features that provide genuine value to users, going beyond simple CRUD operations to deliver insights based on relationships within the data.

## Features

### Comment System
- Users can post comments on ETF pages
- Comments are displayed with username and timestamp
- Comment count is automatically tracked and displayed for each ETF
- Real-time comment count updates using database triggers
- Comment moderation and user authentication

### Database Features
- Automatic comment count tracking using PostgreSQL triggers
- Trigger function `update_comment_count()` increments comment count on new comments
- Comment count is stored in the ETF table and displayed in the UI
