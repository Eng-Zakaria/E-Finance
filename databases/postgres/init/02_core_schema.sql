-- E-Finance Core Banking Schema
-- PostgreSQL Database Schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================
-- USERS TABLE
-- =====================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'customer',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    is_email_verified BOOLEAN DEFAULT FALSE,
    is_phone_verified BOOLEAN DEFAULT FALSE,
    is_2fa_enabled BOOLEAN DEFAULT FALSE,
    totp_secret VARCHAR(255),
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    kyc_level INTEGER DEFAULT 0,
    kyc_verified_at TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    last_login_ip VARCHAR(45),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_status ON users(status);

-- =====================
-- USER PROFILES TABLE
-- =====================
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    date_of_birth DATE,
    gender VARCHAR(20),
    nationality VARCHAR(3),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(3),
    id_type VARCHAR(50),
    id_number VARCHAR(100),
    id_expiry DATE,
    tax_id VARCHAR(50),
    occupation VARCHAR(100),
    employer VARCHAR(255),
    annual_income BIGINT,
    source_of_funds VARCHAR(100),
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);

-- =====================
-- ACCOUNTS TABLE
-- =====================
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_number VARCHAR(20) NOT NULL UNIQUE,
    account_name VARCHAR(255) NOT NULL,
    account_type VARCHAR(30) NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    balance BIGINT NOT NULL DEFAULT 0,
    available_balance BIGINT NOT NULL DEFAULT 0,
    hold_balance BIGINT NOT NULL DEFAULT 0,
    credit_limit BIGINT,
    minimum_balance BIGINT DEFAULT 0,
    interest_rate DECIMAL(5, 4),
    interest_accrued BIGINT DEFAULT 0,
    last_interest_calculated TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    is_primary BOOLEAN DEFAULT FALSE,
    iban VARCHAR(34),
    swift_code VARCHAR(11),
    routing_number VARCHAR(9),
    wallet_address VARCHAR(255),
    blockchain_network VARCHAR(50),
    daily_transfer_limit BIGINT DEFAULT 1000000,
    daily_withdrawal_limit BIGINT DEFAULT 500000,
    monthly_transfer_limit BIGINT DEFAULT 10000000,
    daily_transfer_used BIGINT DEFAULT 0,
    daily_withdrawal_used BIGINT DEFAULT 0,
    monthly_transfer_used BIGINT DEFAULT 0,
    last_limit_reset TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_accounts_user_id ON accounts(user_id);
CREATE INDEX idx_accounts_account_number ON accounts(account_number);
CREATE INDEX idx_accounts_status ON accounts(status);

-- =====================
-- TRANSACTIONS TABLE
-- =====================
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    counterparty_account_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
    reference_number VARCHAR(50) NOT NULL UNIQUE,
    transaction_type VARCHAR(30) NOT NULL,
    channel VARCHAR(20) NOT NULL DEFAULT 'web',
    amount BIGINT NOT NULL,
    currency VARCHAR(10) NOT NULL,
    fee BIGINT DEFAULT 0,
    exchange_rate VARCHAR(50),
    original_amount BIGINT,
    original_currency VARCHAR(10),
    balance_before BIGINT NOT NULL,
    balance_after BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    counterparty_name VARCHAR(255),
    counterparty_bank VARCHAR(255),
    counterparty_account VARCHAR(50),
    counterparty_iban VARCHAR(34),
    counterparty_swift VARCHAR(11),
    blockchain_tx_hash VARCHAR(255),
    blockchain_network VARCHAR(50),
    wallet_address VARCHAR(255),
    gas_fee BIGINT,
    description TEXT,
    memo VARCHAR(255),
    ip_address VARCHAR(45),
    device_id VARCHAR(255),
    device_type VARCHAR(50),
    location_country VARCHAR(3),
    location_city VARCHAR(100),
    geolocation VARCHAR(50),
    risk_level VARCHAR(20) DEFAULT 'low',
    risk_score INTEGER DEFAULT 0,
    fraud_flags JSONB,
    is_suspicious BOOLEAN DEFAULT FALSE,
    reviewed_by UUID,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_notes TEXT,
    aml_check_status VARCHAR(50),
    aml_alert_id VARCHAR(100),
    pep_screening_result VARCHAR(50),
    sanctions_screening_result VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_transactions_account_id ON transactions(account_id);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_type ON transactions(transaction_type);
CREATE INDEX idx_transactions_reference ON transactions(reference_number);
CREATE INDEX idx_transactions_risk_level ON transactions(risk_level);

-- =====================
-- CARDS TABLE
-- =====================
CREATE TABLE cards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    card_number_hash VARCHAR(255) NOT NULL,
    card_number_last_four VARCHAR(4) NOT NULL,
    expiry_month INTEGER NOT NULL,
    expiry_year INTEGER NOT NULL,
    cvv_hash VARCHAR(255) NOT NULL,
    card_type VARCHAR(20) NOT NULL,
    card_network VARCHAR(20) NOT NULL DEFAULT 'visa',
    cardholder_name VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    is_physical BOOLEAN DEFAULT TRUE,
    pin_set BOOLEAN DEFAULT FALSE,
    daily_limit BIGINT DEFAULT 500000,
    transaction_limit BIGINT DEFAULT 100000,
    monthly_limit BIGINT DEFAULT 5000000,
    atm_daily_limit BIGINT DEFAULT 100000,
    daily_spent BIGINT DEFAULT 0,
    monthly_spent BIGINT DEFAULT 0,
    last_limit_reset TIMESTAMP WITH TIME ZONE,
    online_transactions_enabled BOOLEAN DEFAULT TRUE,
    international_transactions_enabled BOOLEAN DEFAULT FALSE,
    contactless_enabled BOOLEAN DEFAULT TRUE,
    atm_withdrawals_enabled BOOLEAN DEFAULT TRUE,
    credit_limit BIGINT,
    current_balance BIGINT DEFAULT 0,
    minimum_payment BIGINT DEFAULT 0,
    due_date TIMESTAMP WITH TIME ZONE,
    billing_address JSONB,
    shipping_address JSONB,
    shipped_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    activated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_cards_user_id ON cards(user_id);
CREATE INDEX idx_cards_account_id ON cards(account_id);
CREATE INDEX idx_cards_card_number_hash ON cards(card_number_hash);

-- =====================
-- FRAUD ALERTS TABLE
-- =====================
CREATE TABLE fraud_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_id UUID REFERENCES transactions(id) ON DELETE SET NULL,
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    flags JSONB,
    risk_score DECIMAL(5, 2),
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    resolved_by UUID,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fraud_alerts_account_id ON fraud_alerts(account_id);
CREATE INDEX idx_fraud_alerts_status ON fraud_alerts(status);
CREATE INDEX idx_fraud_alerts_created_at ON fraud_alerts(created_at);

-- =====================
-- AUDIT LOG TABLE
-- =====================
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- =====================
-- DAILY TRANSACTION SUMMARY (for analytics)
-- =====================
CREATE TABLE daily_transaction_summary (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date DATE NOT NULL UNIQUE,
    total_volume BIGINT DEFAULT 0,
    transaction_count INTEGER DEFAULT 0,
    avg_amount BIGINT DEFAULT 0,
    total_fees BIGINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_daily_summary_date ON daily_transaction_summary(date);

-- =====================
-- USER VELOCITY METRICS (for fraud detection)
-- =====================
CREATE TABLE user_velocity_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    daily_count INTEGER DEFAULT 0,
    daily_volume BIGINT DEFAULT 0,
    UNIQUE(user_id, date)
);

CREATE INDEX idx_velocity_user_date ON user_velocity_metrics(user_id, date);

-- =====================
-- UPDATE TIMESTAMP TRIGGER
-- =====================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_accounts_updated_at
    BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_transactions_updated_at
    BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cards_updated_at
    BEFORE UPDATE ON cards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

