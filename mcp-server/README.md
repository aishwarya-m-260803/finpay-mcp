# FinPay MCP Server

[Model Context Protocol](https://modelcontextprotocol.io/) server for the FinPay platform, backed by PostgreSQL.

> **Status:** Active — 6 read-only MCP tools available.

## Prerequisites

- Python 3.10+
- PostgreSQL 14+ with the FinPay database loaded (see `../database/`)

## Setup

```bash
cd mcp-server
pip install -r requirements.txt

# Ensure DATABASE_URL is set in .env
```

## Run

```bash
python server.py
```

Or via the MCP CLI:

```bash
mcp run server.py
```

## Available MCP Tools

| Tool Name | Parameters | Description |
|---|---|---|
| `search_customers` | `query: str` | Search customers by name, email, or city using partial matching (`ILIKE`) |
| `get_account` | `account_id: int` | Get account details by account ID, including related customer info |
| `get_customer_transactions` | `customer_id: int`, `limit: int = 50` | Get all transactions across all accounts belonging to a customer |
| `get_transaction` | `transaction_id: int` | Get complete details of a single transaction (account, customer, merchant) |
| `get_merchant_transactions` | `merchant_id: int`, `limit: int = 50` | Get all transactions for a specific merchant |
| `get_transaction_summary` | `account_id: int`, `start_date: str?`, `end_date: str?` | Transaction count, sum, and average grouped by transaction type with date filtering |

## Health Check

The server exposes a `health://status` resource that verifies PostgreSQL connectivity.

## Project Structure

```
mcp-server/
├── server.py          # FastMCP entry point with all 6 tools
├── db.py              # asyncpg connection pool management
├── requirements.txt   # mcp<2, asyncpg, python-dotenv
├── .env               # DATABASE_URL configuration
└── README.md
```
