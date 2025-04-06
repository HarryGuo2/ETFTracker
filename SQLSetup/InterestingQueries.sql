-- Query 1: Most Popular ETFs Among Users
-- This query identifies which ETFs are most popular among users and shows their sector composition,
-- helping to understand user preferences and potential market trends.

SELECT 
    e.etf_ticker, 
    e.etf_name, 
    COUNT(DISTINCT ui.user_id) AS interested_users,
    s.sector_name, 
    ehs.sector_weight
FROM 
    hg2736.etf e
JOIN 
    hg2736.user_interest_etf ui ON e.etf_ticker = ui.etf_ticker
JOIN 
    hg2736.etf_has_sector ehs ON e.etf_ticker = ehs.etf_ticker
JOIN 
    hg2736.sector s ON ehs.sector_id = s.sector_id
GROUP BY 
    e.etf_ticker, e.etf_name, s.sector_name, ehs.sector_weight
ORDER BY 
    interested_users DESC, sector_weight DESC;


-- Query 2: Stock Overlap Analysis Between ETFs
-- This query identifies stocks that appear in multiple ETFs and their weights,
-- which is useful for investors to understand potential overexposure to certain stocks.

SELECT 
    s.stock_ticker, 
    s.stock_name, 
    COUNT(DISTINCT sie.etf_ticker) AS etf_count,
    STRING_AGG(DISTINCT e.etf_name, ', ') AS present_in_etfs,
    AVG(sie.stock_weight) AS avg_weight
FROM 
    hg2736.stock s
JOIN 
    hg2736.stock_in_etf sie ON s.stock_ticker = sie.stock_ticker
JOIN 
    hg2736.etf e ON sie.etf_ticker = e.etf_ticker
GROUP BY 
    s.stock_ticker, s.stock_name
HAVING 
    COUNT(DISTINCT sie.etf_ticker) > 1
ORDER BY 
    etf_count DESC, avg_weight DESC
LIMIT 20;


-- Query 3: User Investment Profile Analysis
-- This query analyzes each user's investment preferences by sector exposure,
-- providing insights into user risk profiles and investment strategies.

WITH user_etf_sectors AS (
    SELECT 
        u.user_id,
        u.user_name,
        s.sector_name,
        SUM(ehs.sector_weight) AS total_sector_exposure
    FROM 
        hg2736."User" u
    JOIN 
        hg2736.user_interest_etf uie ON u.user_id = uie.user_id
    JOIN 
        hg2736.etf_has_sector ehs ON uie.etf_ticker = ehs.etf_ticker
    JOIN 
        hg2736.sector s ON ehs.sector_id = s.sector_id
    GROUP BY 
        u.user_id, u.user_name, s.sector_name
)
SELECT 
    user_id,
    user_name,
    sector_name,
    total_sector_exposure,
    RANK() OVER (PARTITION BY user_id ORDER BY total_sector_exposure DESC) AS sector_rank
FROM 
    user_etf_sectors
WHERE 
    RANK() OVER (PARTITION BY user_id ORDER BY total_sector_exposure DESC) <= 3
ORDER BY 
    user_id, sector_rank; 