-- ============================================================
-- FinPay — Database Schema
-- PostgreSQL 14+
-- ============================================================

-- Clean slate (drop in reverse-dependency order)
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS merchants    CASCADE;
DROP TABLE IF EXISTS accounts     CASCADE;
DROP TABLE IF EXISTS customers    CASCADE;

-- ------------------------------------------------------------
-- CUSTOMERS
-- ------------------------------------------------------------
CREATE TABLE customers (
    customer_id   SERIAL        PRIMARY KEY,
    name          VARCHAR(100)  NOT NULL,
    email         VARCHAR(100)  NOT NULL UNIQUE,
    phone         VARCHAR(15)   NOT NULL,
    city          VARCHAR(50)   NOT NULL,
    created_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- ACCOUNTS
-- ------------------------------------------------------------
CREATE TABLE accounts (
    account_id    SERIAL         PRIMARY KEY,
    customer_id   INTEGER        NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    account_type  VARCHAR(20)    NOT NULL CHECK (account_type IN ('savings', 'current', 'wallet')),
    balance       NUMERIC(14,2)  NOT NULL DEFAULT 0 CHECK (balance >= 0),
    currency      VARCHAR(3)     NOT NULL DEFAULT 'INR',
    status        VARCHAR(10)    NOT NULL DEFAULT 'active'
                                 CHECK (status IN ('active', 'frozen', 'closed')),
    created_at    TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- MERCHANTS
-- ------------------------------------------------------------
CREATE TABLE merchants (
    merchant_id    SERIAL       PRIMARY KEY,
    merchant_name  VARCHAR(100) NOT NULL,
    category       VARCHAR(50)  NOT NULL,
    city           VARCHAR(50)  NOT NULL
);

-- ------------------------------------------------------------
-- TRANSACTIONS
-- ------------------------------------------------------------
CREATE TABLE transactions (
    transaction_id    SERIAL         PRIMARY KEY,
    account_id        INTEGER        NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
    merchant_id       INTEGER        REFERENCES merchants(merchant_id) ON DELETE SET NULL,
    transaction_type  VARCHAR(10)    NOT NULL
                                     CHECK (transaction_type IN ('credit', 'debit', 'transfer', 'refund')),
    amount            NUMERIC(14,2)  NOT NULL CHECK (amount > 0),
    currency          VARCHAR(3)     NOT NULL DEFAULT 'INR',
    status            VARCHAR(10)    NOT NULL DEFAULT 'pending'
                                     CHECK (status IN ('success', 'pending', 'failed', 'reversed')),
    transaction_date  TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    description       TEXT
);

-- Indexes for common query patterns
CREATE INDEX idx_accounts_customer       ON accounts(customer_id);
CREATE INDEX idx_accounts_status         ON accounts(status);
CREATE INDEX idx_transactions_account    ON transactions(account_id);
CREATE INDEX idx_transactions_merchant   ON transactions(merchant_id);
CREATE INDEX idx_transactions_status     ON transactions(status);
CREATE INDEX idx_transactions_date       ON transactions(transaction_date);
CREATE INDEX idx_merchants_category      ON merchants(category);
