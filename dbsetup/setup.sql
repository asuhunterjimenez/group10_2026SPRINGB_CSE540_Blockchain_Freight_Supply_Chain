-- Create database
CREATE DATABASE freight_scm_db;

-- Connect to the database
\c freight_scm_db;

-- Enable pgcrypto extension is to encrypt the user password
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =========================
-- Users table creation
-- =========================
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    userrole VARCHAR(50) NOT NULL DEFAULT 'customer',
    account_status VARCHAR(30) NOT NULL DEFAULT 'active',
    company_name VARCHAR(150),
    wallet_address VARCHAR(100) UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- System config table creation
-- =========================
CREATE TABLE system_config (
    config_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    config_description TEXT,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- Example to add users data
-- =========================
INSERT INTO users (
    username,
    email,
    password_hash,
    userrole,
    company_name,
    wallet_address
)
VALUES
(
    'admin_user',
    'admin@freightscm.com',
    crypt('<ReplaceWithAdminPassWord>', gen_salt('bf')),
    'admin',
    'Freight SCM',
    '0xADMIN001'
),
(
    'shipper01',
    'shipper01@acme.com',
    crypt('<ReplaceWithShipperPassword>', gen_salt('bf')),
    'shipper',
    'Acme Freight',
    '0xSHIPPER001'
);

-- =========================
-- Example to add config data
-- =========================
INSERT INTO system_config (config_key, config_value, config_description)
VALUES
    ('max_login_attempts', '5', 'Max failed login attempts');

-- =========================
-- Some sample queries
-- =========================

-- To view users
SELECT * FROM users;

-- To view config
SELECT * FROM system_config;

-- How to check Login
SELECT *
FROM users
WHERE username = 'admin_user'
  AND account_status = 'active'
  AND password_hash = crypt('<ReplaceWithAdminPassWord>', password_hash);