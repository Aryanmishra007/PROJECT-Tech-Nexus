-- ═══════════════════════════════════════════════════════════════════════
-- NexaAI MySQL Database Setup
-- Run this script in MySQL Workbench before starting the application
-- ═══════════════════════════════════════════════════════════════════════

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS projectnexai_ai
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- Switch to the database
USE projectnexai_ai;

-- Grant permissions (if needed)
-- GRANT ALL PRIVILEGES ON projectnexai_ai.* TO 'root'@'localhost';
-- FLUSH PRIVILEGES;

-- Note: The Flask application will automatically create the tables
-- when you run app.py. This script just ensures the database exists.

SELECT 'Database projectnexai_ai created successfully!' AS status;
