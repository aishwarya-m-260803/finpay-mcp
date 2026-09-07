# FinPay — Database Setup

PostgreSQL database schema and seed data for a fintech payments platform.

## Prerequisites

- PostgreSQL 14+

## Quick Start

```bash
# Create the database
createdb finpay

# Load schema and seed data
psql -d finpay -f database/schema.sql
psql -d finpay -f database/seed.sql
```

> Update `.env` with your actual PostgreSQL credentials if scripting against the database.

## Schema

```
customers ──< accounts ──< transactions >── merchants
```

### customers

| Column | Type | Constraints |
|---|---|---|
| `customer_id` | `SERIAL` | **PK** |
| `name` | `VARCHAR(100)` | `NOT NULL` |
| `email` | `VARCHAR(100)` | `NOT NULL`, `UNIQUE` |
| `phone` | `VARCHAR(15)` | `NOT NULL` |
| `city` | `VARCHAR(50)` | `NOT NULL` |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, default `NOW()` |

### accounts

| Column | Type | Constraints |
|---|---|---|
| `account_id` | `SERIAL` | **PK** |
| `customer_id` | `INTEGER` | **FK → customers**, `NOT NULL` |
| `account_type` | `VARCHAR(20)` | `CHECK (savings, current, wallet)` |
| `balance` | `NUMERIC(14,2)` | `≥ 0` |
| `currency` | `VARCHAR(3)` | default `INR` |
| `status` | `VARCHAR(10)` | `CHECK (active, frozen, closed)` |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, default `NOW()` |

### merchants

| Column | Type | Constraints |
|---|---|---|
| `merchant_id` | `SERIAL` | **PK** |
| `merchant_name` | `VARCHAR(100)` | `NOT NULL` |
| `category` | `VARCHAR(50)` | `NOT NULL` |
| `city` | `VARCHAR(50)` | `NOT NULL` |

### transactions

| Column | Type | Constraints |
|---|---|---|
| `transaction_id` | `SERIAL` | **PK** |
| `account_id` | `INTEGER` | **FK → accounts**, `NOT NULL` |
| `merchant_id` | `INTEGER` | **FK → merchants**, nullable |
| `transaction_type` | `VARCHAR(10)` | `CHECK (credit, debit, transfer, refund)` |
| `amount` | `NUMERIC(14,2)` | `> 0` |
| `currency` | `VARCHAR(3)` | default `INR` |
| `status` | `VARCHAR(10)` | `CHECK (success, pending, failed, reversed)` |
| `transaction_date` | `TIMESTAMPTZ` | `NOT NULL`, default `NOW()` |
| `description` | `TEXT` | — |

## Seed Data Summary

| Table | Rows | Notes |
|---|---|---|
| `customers` | 15 | Indian names across Bangalore, Hyderabad, Chennai, Delhi, Pune, Mumbai, Noida, Gurugram |
| `accounts` | 20 | Mix of savings / current / wallet; 5 customers have 2 accounts |
| `merchants` | 15 | E-commerce, food delivery, travel, rent, telecom, subscriptions, retail, utilities, fuel, healthcare |
| `transactions` | 70 | Realistic amounts with credits, debits, 1 refund, 1 transfer, 1 failed, 1 pending |

All account balances are consistent with the sum of their successful transactions.

## Project Structure

```
├── .env                   # PostgreSQL connection string config
├── README.md
└── database/
    ├── schema.sql         # Table definitions, constraints, indexes
    └── seed.sql           # Realistic Indian fintech test data
```

## License

MIT
