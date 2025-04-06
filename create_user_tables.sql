-- Create Users table for authentication
CREATE TABLE IF NOT EXISTS Users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    user_key VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table to track user ETF interests/likes
CREATE TABLE IF NOT EXISTS User_Likes_ETF (
    user_id INTEGER REFERENCES Users(user_id),
    etf_ticker VARCHAR REFERENCES ETF(etf_ticker),
    liked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, etf_ticker)
); 