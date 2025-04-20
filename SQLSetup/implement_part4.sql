-- Set the search path to your schema
SET search_path TO hg2736;

-- 1. Create a composite type for ETF performance metrics
CREATE TYPE etf_performance AS (
    volatility DECIMAL,
    sharpe_ratio DECIMAL,
    max_drawdown DECIMAL,
    inception_date DATE,
    last_updated TIMESTAMP
);

-- 2. Create a table using the composite type
CREATE TABLE etf_performance_metrics (
    etf_ticker VARCHAR(10) PRIMARY KEY,
    volatility DECIMAL,
    sharpe_ratio DECIMAL,
    max_drawdown DECIMAL,
    inception_date DATE,
    last_updated TIMESTAMP
);

-- 3. Create a function to calculate performance metrics
CREATE OR REPLACE FUNCTION calculate_performance_metrics(
    p_ticker VARCHAR(10),
    p_returns DECIMAL[]
) RETURNS etf_performance AS $$
DECLARE
    v_volatility DECIMAL;
    v_sharpe_ratio DECIMAL;
    v_max_drawdown DECIMAL;
    v_returns DECIMAL[];
    v_avg_return DECIMAL;
    v_std_dev DECIMAL;
    v_min_return DECIMAL;
BEGIN
    -- Calculate average return
    SELECT AVG(r) INTO v_avg_return
    FROM unnest(p_returns) AS r;
    
    -- Calculate standard deviation (volatility)
    SELECT SQRT(AVG(POWER(r - v_avg_return, 2))) INTO v_std_dev
    FROM unnest(p_returns) AS r;
    
    -- Calculate maximum drawdown
    WITH returns AS (
        SELECT r, ROW_NUMBER() OVER () AS idx
        FROM unnest(p_returns) AS r
    )
    SELECT MIN(1 - (r2.r / r1.r)) INTO v_max_drawdown
    FROM returns r1
    JOIN returns r2 ON r2.idx > r1.idx;
    
    -- Calculate Sharpe ratio (assuming risk-free rate of 0.02 or 2%)
    v_sharpe_ratio := (v_avg_return - 0.02) / NULLIF(v_std_dev, 0);
    
    -- Return the composite type
    RETURN ROW(
        v_std_dev,          -- volatility
        v_sharpe_ratio,     -- sharpe ratio
        v_max_drawdown,     -- max drawdown
        CURRENT_DATE,       -- inception date
        CURRENT_TIMESTAMP   -- last updated
    )::etf_performance;
END;
$$ LANGUAGE plpgsql;

-- 4. Create a trigger function to automatically update performance metrics
CREATE OR REPLACE FUNCTION update_etf_performance_metrics()
RETURNS TRIGGER AS $$
BEGIN
    -- Only proceed if annual_returns is updated
    IF TG_OP = 'UPDATE' AND NEW.annual_returns IS NOT NULL THEN
        -- Calculate new performance metrics
        INSERT INTO etf_performance_metrics
        SELECT NEW.etf_ticker, (calculate_performance_metrics(NEW.etf_ticker, NEW.annual_returns)).*
        ON CONFLICT (etf_ticker) DO UPDATE
        SET 
            volatility = EXCLUDED.volatility,
            sharpe_ratio = EXCLUDED.sharpe_ratio,
            max_drawdown = EXCLUDED.max_drawdown,
            last_updated = EXCLUDED.last_updated;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 5. Create the trigger
CREATE TRIGGER update_performance_metrics
AFTER INSERT OR UPDATE ON etf
FOR EACH ROW
EXECUTE FUNCTION update_etf_performance_metrics();

-- 6. Example queries to demonstrate the features

-- Full-text search example
SELECT etf_ticker, etf_name, etf_review
FROM etf
WHERE to_tsvector('english', etf_review) @@ to_tsquery('market & exposure');

-- Array operations example
SELECT 
    etf_ticker,
    etf_name,
    annual_returns[1] AS year_1_return,
    annual_returns[2] AS year_2_return,
    (annual_returns[1] + annual_returns[2]) / 2 AS avg_2year_return
FROM etf
WHERE annual_returns IS NOT NULL;

-- Composite type query example
SELECT 
    e.etf_ticker,
    e.etf_name,
    p.volatility,
    p.sharpe_ratio,
    p.max_drawdown,
    p.last_updated
FROM etf e
JOIN etf_performance_metrics p ON e.etf_ticker = p.etf_ticker
WHERE p.sharpe_ratio > 0.5
ORDER BY p.sharpe_ratio DESC;

-- Combined query using all features
SELECT 
    e.etf_ticker,
    e.etf_name,
    e.etf_review,
    array_to_string(e.annual_returns, ', ') AS returns,
    p.volatility,
    p.sharpe_ratio,
    p.max_drawdown
FROM etf e
JOIN etf_performance_metrics p ON e.etf_ticker = p.etf_ticker
WHERE to_tsvector('english', e.etf_review) @@ to_tsquery('growth & technology')
AND p.sharpe_ratio > 0.5
ORDER BY p.sharpe_ratio DESC; 