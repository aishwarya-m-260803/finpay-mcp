# 💳 FinPay — AI-Powered Financial Assistant (MCP + Gemini + Django + React)

FinPay is an enterprise-grade AI financial chatbot that enables users to query complex financial data—such as customer profiles, bank account balances, transaction histories, merchant analytics, and spending summaries—using natural language.

Powered by the **Model Context Protocol (MCP)**, **Google Gemini 3.6 Flash**, **Django REST Framework**, and a custom **React Banking UI**, FinPay safely bridges large language models to a read-only PostgreSQL database via strictly typed tool definitions.

---

## 🏛️ System Architecture

```
┌─────────────────┐       HTTP / JSON        ┌──────────────────────┐
│  React Frontend │ ───────────────────────> │  Django REST Backend │
│  (Vite + CSS)   │ <─────────────────────── │  (POST /api/chat/)   │
└─────────────────┘                          └──────────┬───────────┘
                                                        │ Async Function Calling
                                                        ▼
┌─────────────────┐       MCP Stdio Protocol ┌──────────────────────┐
│ PostgreSQL DB   │ <─────────────────────── │ Gemini 3.6 Flash LLM │
│ (finpay schema) │ <── asyncpg Pool ─────── │ + FastMCP Client     │
└─────────────────┘                          └──────────────────────┘
```

---

## ✨ Key Features & Engineering Highlights

### 1. 🤖 Dynamic MCP Tool Calling & Reasoning
- **FastMCP Protocol**: Bridges Gemini directly to PostgreSQL over stdio using the official Model Context Protocol standard.
- **Dynamic Tool Schema Translation**: Automatically converts Python tool signatures from `mcp-server/server.py` into Gemini `FunctionDeclaration` specs at runtime.
- **Multi-Step Reasoning**: Gemini autonomously chains multiple MCP tools together (e.g. searching for a customer by name → retrieving their account ID → calculating spending breakdown).

### 2. 🛡️ Robust Async TaskGroup & Exception Unwrapping
- **Python 3.11+ TaskGroup Safety**: Resolves `asyncio.TaskGroup` / `ExceptionGroup` crashes that occur inside async MCP stdio streams.
- **Recursive Unwrapper (`_unwrap_exception_group`)**: Recursively extracts root sub-exceptions from `ExceptionGroup` trees to deliver accurate error diagnoses and clean HTTP error codes.

### 3. 🎯 4-Tier MCP Error Boundary System
FinPay enforces strict error taxonomy across both backend APIs and the frontend chat UI:
- **1. API Quota Exhaustion (`MCPQuotaError` / HTTP 429)**: Triggers amber alert when LLM quotas or keys are exhausted without wasteful retries.
- **2. MCP Rule Boundary (`MCPBoundaryError` / HTTP 403)**: Red alert when queries request unauthorized scope or violate MCP safety guidelines.
- **3. Parameter Mismatch (`MCPParameterError` / HTTP 400)**: Orange alert when tool arguments fail type or range validation.
- **4. Internal Fault (`MCPToolError` / HTTP 500)**: Muted red alert when database connections or internal executions fail.

### 4. 🔄 Resilient Model Fallback Cascade
- **Automatic Model Failover**: Gracefully attempts execution using `gemini-3.6-flash` → `gemini-2.0-flash` → `gemini-1.5-flash` → `gemini-2.0-flash-lite`.
- **Deprecation Intelligence**: Automatically identifies and bypasses retired or 404 models without breaking active user sessions.

### 5. 🎨 Modern Fintech Visual Theme
- **Banking Design Palette**: Dark emerald fintech aesthetic (`#0B1110` Canvas, `#111B18` Cards, `#19C37D` Primary Emerald Accent, `#4FD1C5` Secondary Teal Accent).
- **Typography & Markdown**: Custom typography using the Google **Manrope** font family alongside rich markdown rendering (`react-markdown` formatted tables, bold indicators, lists, and code blocks).

---

## 🛠️ MCP Tool Definitions

The FinPay FastMCP server (`mcp-server/server.py`) provides 6 read-only tools:

| Tool Name | Parameters | Description |
|---|---|---|
| `search_customers` | `query: str` | Search customers by name, email, or city using partial matching (`ILIKE`). |
| `get_account` | `account_id: int` | Retrieve account balance, currency, type, and owning customer info by account ID. |
| `get_customer_transactions` | `customer_id: int`, `limit: int = 50` | Retrieve transaction history across all accounts belonging to a customer. |
| `get_transaction` | `transaction_id: int` | Get complete details of a single transaction (account, customer, merchant info). |
| `get_merchant_transactions` | `merchant_id: int`, `limit: int = 50` | Get all transactions associated with a specific merchant. |
| `get_transaction_summary` | `account_id: int`, `start_date: str?`, `end_date: str?` | Compute total spend, transaction counts, and averages grouped by transaction type (`debit`, `credit`, `transfer`, `refund`). |

---

## 💬 Example Supported Queries

Users can ask natural language questions such as:

- **Customer Search**: *"Find all customers living in Chennai"* or *"Search for customer Rahul"*
- **Account Enquiries**: *"What is the current balance of account 101?"*
- **Transaction Audit**: *"Show me the last 10 transactions for customer 12"*
- **Merchant Tracking**: *"List all purchases made at merchant #5"*
- **Analytics & Breakdown**: *"What is the total spending on account 200 between 2026-01-01 and 2026-06-30?"*
- **Multi-Step Queries**: *"Find customer 'Sarah' and summarize her spending history"*

---

## 📂 Project Structure

```
finpay-mcp/
├── backend/                  # Django REST API Backend
│   ├── dashboard/            # Core dashboard & chat API app
│   │   ├── api_views.py      # /api/chat/ endpoint with ExceptionGroup unwrapping
│   │   ├── models.py         # Unmanaged Django ORM models (managed = False)
│   │   └── urls.py           # REST endpoints mapping
│   ├── finpay/               # Django project settings & configuration
│   └── manage.py
├── frontend/                 # React (Vite) Chatbot Frontend
│   ├── src/
│   │   ├── App.jsx           # FinPay AI Chat interface & state management
│   │   ├── index.css         # Custom Emerald & Dark Banking theme CSS
│   │   └── main.jsx
│   └── package.json
├── client/                   # Gemini LLM + MCP Client bridge
│   ├── llm_runner.py         # Gemini 3.6 Flash tool calling & fallback cascade
│   ├── mcp_client.py         # MCP stdio ClientSession wrapper
│   └── .env                  # GEMINI_API_KEY & model configurations
├── mcp-server/               # FastMCP Python Server
│   ├── server.py             # 6 read-only MCP tool implementations
│   ├── db.py                 # asyncpg database connection pool
│   └── requirements.txt
└── database/                 # PostgreSQL Database Setup
    ├── schema.sql            # Customers, accounts, merchants, transactions schema
    └── seed.sql              # Realistic seed data (Indian names, cities, transactions)
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.10+** (Python 3.11+ recommended)
- **Node.js 18+**
- **PostgreSQL 14+**
- **Google Gemini API Key**

### 1. Database Setup
```bash
# Create database and seed tables
createdb finpay
psql -d finpay -f database/schema.sql
psql -d finpay -f database/seed.sql
```

### 2. Backend & Client Configuration
Configure `client/.env` and `mcp-server/.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.6-flash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/finpay
```

Install backend dependencies and run Django dev server:
```bash
cd backend
pip install -r requirements.txt
python manage.py runserver
```

### 3. Frontend Setup
Install frontend dependencies and start Vite dev server:
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser to interact with **FinPay AI**!

---

## 📜 License

MIT License. Designed for demonstration of Model Context Protocol (MCP) integrations with LLM agents.

