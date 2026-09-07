-- ============================================================
-- FinPay — Seed Data
-- Run AFTER schema.sql
-- ============================================================
-- Balance consistency rule (for successful transactions only):
--   credit, refund  → +balance
--   debit, transfer → −balance
--   pending / failed → no effect on balance
-- ============================================================

-- ------------------------------------------------------------
-- CUSTOMERS  (15 rows)
-- ------------------------------------------------------------
INSERT INTO customers (name, email, phone, city) VALUES
('Arjun Sharma',     'arjun.sharma@email.com',    '9876543210', 'Bangalore'),
('Priya Nair',       'priya.nair@email.com',      '9876543211', 'Bangalore'),
('Vikram Patel',     'vikram.patel@email.com',     '9876543212', 'Hyderabad'),
('Ananya Iyer',      'ananya.iyer@email.com',      '9876543213', 'Chennai'),
('Rahul Gupta',      'rahul.gupta@email.com',      '9876543214', 'Noida'),
('Meera Reddy',      'meera.reddy@email.com',      '9876543215', 'Hyderabad'),
('Karthik Menon',    'karthik.menon@email.com',    '9876543216', 'Bangalore'),
('Sneha Deshmukh',   'sneha.deshmukh@email.com',   '9876543217', 'Pune'),
('Aditya Singh',     'aditya.singh@email.com',     '9876543218', 'Delhi'),
('Divya Krishnan',   'divya.krishnan@email.com',   '9876543219', 'Chennai'),
('Rohan Joshi',      'rohan.joshi@email.com',      '9876543220', 'Pune'),
('Lakshmi Bhat',     'lakshmi.bhat@email.com',     '9876543221', 'Bangalore'),
('Suresh Kumar',     'suresh.kumar@email.com',     '9876543222', 'Mumbai'),
('Neha Agarwal',     'neha.agarwal@email.com',     '9876543223', 'Delhi'),
('Farhan Sheikh',    'farhan.sheikh@email.com',     '9876543224', 'Mumbai');

-- ------------------------------------------------------------
-- MERCHANTS  (15 rows)
-- ------------------------------------------------------------
INSERT INTO merchants (merchant_name, category, city) VALUES
('Amazon India',       'E-commerce',    'Mumbai'),       -- 1
('Swiggy',             'Food Delivery', 'Bangalore'),    -- 2
('Flipkart',           'E-commerce',    'Bangalore'),    -- 3
('Zomato',             'Food Delivery', 'Gurugram'),     -- 4
('IRCTC',              'Travel',        'Delhi'),        -- 5
('NoBroker',           'Rent/Housing',  'Bangalore'),    -- 6
('BigBasket',          'Retail',        'Bangalore'),    -- 7
('Jio',                'Telecom',       'Mumbai'),       -- 8
('MakeMyTrip',         'Travel',        'Gurugram'),     -- 9
('Netflix India',      'Subscription',  'Mumbai'),       -- 10
('Spotify India',      'Subscription',  'Mumbai'),       -- 11
('DMart',              'Retail',        'Pune'),         -- 12
('Tata Power',         'Utilities',     'Mumbai'),       -- 13
('Indian Oil',         'Fuel',          'Delhi'),        -- 14
('Apollo Pharmacy',    'Healthcare',    'Chennai');      -- 15

-- ------------------------------------------------------------
-- ACCOUNTS  (20 rows)
-- Balances are consistent with the transactions seeded below.
-- ------------------------------------------------------------
INSERT INTO accounts (customer_id, account_type, balance, currency, status) VALUES
-- Acct  1: 50000 − 1299 − 450 − 2500 = 45751
( 1, 'savings', 45751.00, 'INR', 'active'),
-- Acct  2: 150000 − 35000 − 899 − 1500 = 112601
( 2, 'current', 112601.00, 'INR', 'active'),
-- Acct  3: 25000 − 599 − 3200 + 12000 = 33201
( 3, 'savings', 33201.00, 'INR', 'active'),
-- Acct  4: 5000 − 250 − 180 − 99 = 4471
( 4, 'wallet',  4471.00, 'INR', 'active'),
-- Acct  5: 75000 − 15000 − 2999 − 1200 = 55801
( 5, 'savings', 55801.00, 'INR', 'active'),
-- Acct  6: 200000 − 45000 − 8500 − 1999 = 144501
( 6, 'current', 144501.00, 'INR', 'active'),
-- Acct  7: 30000 − 499 − 350 = 29151  (failed txn ignored)
( 7, 'savings', 29151.00, 'INR', 'active'),
-- Acct  8: 10000 − 399 − 1500 = 8101
( 8, 'wallet',  8101.00, 'INR', 'active'),
-- Acct  9: 45000 − 6999 − 2200 = 35801
( 9, 'savings', 35801.00, 'INR', 'active'),
-- Acct 10: 180000 − 40000 − 3500 − 12000 = 124500
(10, 'current', 124500.00, 'INR', 'active'),
-- Acct 11: 60000 − 1799 − 850 = 57351
(11, 'savings', 57351.00, 'INR', 'active'),
-- Acct 12: 3000 − 199 − 299 = 2502
(11, 'wallet',  2502.00, 'INR', 'active'),
-- Acct 13: 85000 − 4500 − 1100 + 1100 = 80500
(12, 'savings', 80500.00, 'INR', 'active'),
-- Acct 14: 120000 − 25000 − 7500 = 87500
(12, 'current', 87500.00, 'INR', 'active'),
-- Acct 15: 40000 − 2499 − 650 = 36851
(13, 'savings', 36851.00, 'INR', 'active'),
-- Acct 16: 8000 − 450 = 7550  (pending txn ignored)
(13, 'wallet',  7550.00, 'INR', 'active'),
-- Acct 17: 175000 − 50000 − 5200 = 119800
(14, 'current', 119800.00, 'INR', 'active'),
-- Acct 18: 55000 − 999 − 3800 = 50201
(14, 'savings', 50201.00, 'INR', 'active'),
-- Acct 19: 90000 − 8999 − 15000 + 5000 = 71001
(15, 'savings', 71001.00, 'INR', 'active'),
-- Acct 20: 2000 − 149 − 350 = 1501
(15, 'wallet',  1501.00, 'INR', 'active');

-- ------------------------------------------------------------
-- TRANSACTIONS  (70 rows)
-- Grouped by account for auditability.
-- Only successful credit/refund add to balance;
-- only successful debit/transfer subtract from balance.
-- Failed and pending transactions have no balance effect.
-- ------------------------------------------------------------
INSERT INTO transactions (account_id, merchant_id, transaction_type, amount, currency, status, transaction_date, description) VALUES

-- ── Account 1 (savings, Arjun Sharma) ── balance: 45751 ──
( 1, NULL,  'credit',  50000.00, 'INR', 'success', '2026-07-01 09:00:00+05:30', 'Opening deposit'),
( 1,    1,  'debit',    1299.00, 'INR', 'success', '2026-07-05 14:22:00+05:30', 'Amazon purchase — electronics'),
( 1,    2,  'debit',     450.00, 'INR', 'success', '2026-07-12 20:15:00+05:30', 'Swiggy food order'),
( 1,    5,  'debit',    2500.00, 'INR', 'success', '2026-07-20 11:30:00+05:30', 'IRCTC train ticket booking'),

-- ── Account 2 (current, Priya Nair) ── balance: 112601 ──
( 2, NULL,  'credit', 150000.00, 'INR', 'success', '2026-07-01 09:00:00+05:30', 'Salary credit — July'),
( 2,    6,  'debit',   35000.00, 'INR', 'success', '2026-07-05 10:00:00+05:30', 'Monthly rent payment via NoBroker'),
( 2,    3,  'debit',     899.00, 'INR', 'success', '2026-07-10 16:45:00+05:30', 'Flipkart order — books'),
( 2,    8,  'debit',    1500.00, 'INR', 'success', '2026-07-15 12:00:00+05:30', 'Jio annual recharge plan'),

-- ── Account 3 (savings, Vikram Patel) ── balance: 33201 ──
( 3, NULL,  'credit',  25000.00, 'INR', 'success', '2026-07-02 10:30:00+05:30', 'Opening deposit'),
( 3,   10,  'debit',     599.00, 'INR', 'success', '2026-07-08 08:00:00+05:30', 'Netflix monthly subscription'),
( 3,    7,  'debit',    3200.00, 'INR', 'success', '2026-07-14 17:20:00+05:30', 'BigBasket — household essentials'),
( 3, NULL,  'credit',  12000.00, 'INR', 'success', '2026-08-01 09:00:00+05:30', 'Salary credit — August'),

-- ── Account 4 (wallet, Ananya Iyer) ── balance: 4471 ──
( 4, NULL,  'credit',   5000.00, 'INR', 'success', '2026-07-03 11:00:00+05:30', 'Wallet top-up via UPI'),
( 4,    2,  'debit',     250.00, 'INR', 'success', '2026-07-09 13:30:00+05:30', 'Swiggy lunch order'),
( 4,    4,  'debit',     180.00, 'INR', 'success', '2026-07-16 19:45:00+05:30', 'Zomato dinner order'),
( 4,   11,  'debit',      99.00, 'INR', 'success', '2026-07-22 10:00:00+05:30', 'Spotify premium subscription'),

-- ── Account 5 (savings, Rahul Gupta) ── balance: 55801 ──
( 5, NULL,  'credit',  75000.00, 'INR', 'success', '2026-07-01 09:00:00+05:30', 'Salary credit — July'),
( 5,    5,  'debit',   15000.00, 'INR', 'success', '2026-07-06 15:30:00+05:30', 'IRCTC Rajdhani express ticket'),
( 5,    1,  'debit',    2999.00, 'INR', 'success', '2026-07-18 22:10:00+05:30', 'Amazon — home appliance'),
( 5,   12,  'debit',    1200.00, 'INR', 'success', '2026-07-25 11:00:00+05:30', 'DMart monthly groceries'),

-- ── Account 6 (current, Meera Reddy) ── balance: 144501 ──
( 6, NULL,  'credit', 200000.00, 'INR', 'success', '2026-07-01 09:00:00+05:30', 'Business income credit'),
( 6,    6,  'debit',   45000.00, 'INR', 'success', '2026-07-05 10:00:00+05:30', 'Office rent payment'),
( 6,   13,  'debit',    8500.00, 'INR', 'success', '2026-07-12 14:00:00+05:30', 'Tata Power — electricity bill'),
( 6,    3,  'debit',    1999.00, 'INR', 'success', '2026-07-20 18:30:00+05:30', 'Flipkart — office supplies'),

-- ── Account 7 (savings, Karthik Menon) ── balance: 29151 ──
( 7, NULL,  'credit',  30000.00, 'INR', 'success', '2026-07-02 09:30:00+05:30', 'Opening deposit'),
( 7,   10,  'debit',     499.00, 'INR', 'success', '2026-07-10 08:15:00+05:30', 'Netflix standard subscription'),
( 7,    4,  'debit',     350.00, 'INR', 'success', '2026-07-17 13:00:00+05:30', 'Zomato lunch order'),
( 7,   14,  'debit',    5000.00, 'INR', 'failed',  '2026-07-24 16:40:00+05:30', 'Indian Oil fuel purchase — card declined'),

-- ── Account 8 (wallet, Sneha Deshmukh) ── balance: 8101 ──
( 8, NULL,  'credit',  10000.00, 'INR', 'success', '2026-07-03 10:00:00+05:30', 'Wallet top-up via net banking'),
( 8,    2,  'debit',     399.00, 'INR', 'success', '2026-07-11 12:45:00+05:30', 'Swiggy — quick delivery order'),
( 8,   15,  'debit',    1500.00, 'INR', 'success', '2026-07-19 15:30:00+05:30', 'Apollo Pharmacy — medicines'),

-- ── Account 9 (savings, Aditya Singh) ── balance: 35801 ──
( 9, NULL,  'credit',  45000.00, 'INR', 'success', '2026-07-02 09:00:00+05:30', 'Salary credit — July'),
( 9,    1,  'debit',    6999.00, 'INR', 'success', '2026-07-08 21:00:00+05:30', 'Amazon — smartphone accessories'),
( 9,    7,  'debit',    2200.00, 'INR', 'success', '2026-07-22 18:00:00+05:30', 'BigBasket — weekly essentials'),

-- ── Account 10 (current, Divya Krishnan) ── balance: 124500 ──
(10, NULL,  'credit', 180000.00, 'INR', 'success', '2026-07-01 09:00:00+05:30', 'Salary credit — July'),
(10,    6,  'debit',   40000.00, 'INR', 'success', '2026-07-05 10:30:00+05:30', 'Monthly rent payment'),
(10,    8,  'debit',    3500.00, 'INR', 'success', '2026-07-13 11:00:00+05:30', 'Jio Fiber annual plan'),
(10,    5,  'debit',   12000.00, 'INR', 'success', '2026-07-28 14:20:00+05:30', 'Holiday train tickets — IRCTC'),

-- ── Account 11 (savings, Rohan Joshi) ── balance: 57351 ──
(11, NULL,  'credit',  60000.00, 'INR', 'success', '2026-07-03 09:00:00+05:30', 'Salary credit — July'),
(11,    3,  'debit',    1799.00, 'INR', 'success', '2026-07-09 10:15:00+05:30', 'Flipkart — clothing'),
(11,    4,  'debit',     850.00, 'INR', 'success', '2026-07-21 12:30:00+05:30', 'Zomato — team lunch order'),

-- ── Account 12 (wallet, Rohan Joshi) ── balance: 2502 ──
(12, NULL,  'credit',   3000.00, 'INR', 'success', '2026-07-04 14:00:00+05:30', 'Wallet top-up'),
(12,   11,  'debit',     199.00, 'INR', 'success', '2026-07-10 09:00:00+05:30', 'Spotify monthly plan'),
(12,    2,  'debit',     299.00, 'INR', 'success', '2026-07-18 20:30:00+05:30', 'Swiggy — snacks order'),

-- ── Account 13 (savings, Lakshmi Bhat) ── balance: 80500 ──
(13, NULL,  'credit',  85000.00, 'INR', 'success', '2026-07-01 09:00:00+05:30', 'Salary credit — July'),
(13,    9,  'debit',    4500.00, 'INR', 'success', '2026-07-07 17:00:00+05:30', 'MakeMyTrip hotel booking'),
(13,   12,  'debit',    1100.00, 'INR', 'success', '2026-07-15 11:30:00+05:30', 'DMart household shopping'),
(13,   12,  'refund',   1100.00, 'INR', 'success', '2026-07-18 16:00:00+05:30', 'DMart — order return refund'),

-- ── Account 14 (current, Lakshmi Bhat) ── balance: 87500 ──
(14, NULL,  'credit', 120000.00, 'INR', 'success', '2026-07-02 09:30:00+05:30', 'Business account opening deposit'),
(14,    6,  'debit',   25000.00, 'INR', 'success', '2026-07-05 10:00:00+05:30', 'Office space rent'),
(14,   13,  'debit',    7500.00, 'INR', 'success', '2026-07-15 14:30:00+05:30', 'Tata Power — commercial electricity'),

-- ── Account 15 (savings, Suresh Kumar) ── balance: 36851 ──
(15, NULL,  'credit',  40000.00, 'INR', 'success', '2026-07-03 09:00:00+05:30', 'Opening deposit'),
(15,    1,  'debit',    2499.00, 'INR', 'success', '2026-07-12 19:45:00+05:30', 'Amazon — kitchen appliance'),
(15,   15,  'debit',     650.00, 'INR', 'success', '2026-07-20 10:30:00+05:30', 'Apollo Pharmacy — supplements'),

-- ── Account 16 (wallet, Suresh Kumar) ── balance: 7550 ──
(16, NULL,  'credit',   8000.00, 'INR', 'success', '2026-07-04 12:00:00+05:30', 'Wallet top-up via net banking'),
(16,    4,  'debit',     450.00, 'INR', 'success', '2026-07-14 18:15:00+05:30', 'Zomato evening snacks'),
(16,    2,  'debit',    1200.00, 'INR', 'pending', '2026-08-02 21:00:00+05:30', 'Swiggy — order processing'),

-- ── Account 17 (current, Neha Agarwal) ── balance: 119800 ──
(17, NULL,  'credit', 175000.00, 'INR', 'success', '2026-07-01 09:00:00+05:30', 'Salary credit — July'),
(17,    6,  'debit',   50000.00, 'INR', 'success', '2026-07-05 10:00:00+05:30', 'Premium apartment rent'),
(17,   14,  'debit',    5200.00, 'INR', 'success', '2026-07-16 08:30:00+05:30', 'Indian Oil — monthly fuel fill-up'),

-- ── Account 18 (savings, Neha Agarwal) ── balance: 50201 ──
(18, NULL,  'credit',  55000.00, 'INR', 'success', '2026-07-02 09:00:00+05:30', 'Savings deposit'),
(18,   10,  'debit',     999.00, 'INR', 'success', '2026-07-08 08:00:00+05:30', 'Netflix premium plan'),
(18,    7,  'debit',    3800.00, 'INR', 'success', '2026-07-23 16:00:00+05:30', 'BigBasket — monthly household supplies'),

-- ── Account 19 (savings, Farhan Sheikh) ── balance: 71001 ──
(19, NULL,  'credit',  90000.00, 'INR', 'success', '2026-07-01 09:00:00+05:30', 'Salary credit — July'),
(19,    9,  'debit',    8999.00, 'INR', 'success', '2026-07-10 22:00:00+05:30', 'MakeMyTrip flight booking'),
(19, NULL, 'transfer',  15000.00, 'INR', 'success', '2026-07-20 14:00:00+05:30', 'Fund transfer to external account'),
(19, NULL,  'credit',   5000.00, 'INR', 'success', '2026-08-01 11:30:00+05:30', 'Transfer received from joint account'),

-- ── Account 20 (wallet, Farhan Sheikh) ── balance: 1501 ──
(20, NULL,  'credit',   2000.00, 'INR', 'success', '2026-07-05 15:00:00+05:30', 'Wallet top-up'),
(20,   11,  'debit',     149.00, 'INR', 'success', '2026-07-12 09:00:00+05:30', 'Spotify individual plan'),
(20,    2,  'debit',     350.00, 'INR', 'success', '2026-07-22 23:15:00+05:30', 'Swiggy late-night snacks');
