# FinPay — Natural Language Financial Intelligence System

FinPay is an enterprise-grade AI chatbot system that enables natural language querying over relational financial data. Built on a modular, decoupled architecture, FinPay pairs a **React** single-page frontend with a **Django REST API** backend, an autonomous **AI Agent**, a locally hosted **Qwen 3.5 (9B)** LLM served via **Ollama**, and a secure **Model Context Protocol (MCP)** server backed by **PostgreSQL**.

---

## 🎯 Problem Statement & Overview

Financial databases store critical transactional and account data across multiple relational tables (`customers`, `accounts`, `merchants`, `transactions`). Non-technical stakeholders (support agents, compliance teams, account managers) often need immediate answers to queries like:
- *"What is Arjun Sharma's current balance and recent transactions?"*
- *"Show me all recent transactions at Amazon India."*
- *"What is the total spending summary for customer CUST-001?"*

Traditionally, answering these questions required writing manual SQL queries or relying on business intelligence engineers. FinPay solves this by translating natural language queries into safe, multi-tool database operations executed via an AI Agent using the Model Context Protocol (MCP), ensuring strict read-only access and zero exposure to raw database credentials or arbitrary SQL execution.

---

## 🚀 Key Capabilities

- **Natural Language Data Retrieval**: Seamless translation of conversational queries into multi-step database tool calls.
- **Autonomous Multi-Tool Orchestration**: Resolves complex entity chains (e.g., searching customer by name → retrieving account → fetching transaction history).
- **Multi-Turn Context & Coreference Resolution**: Maintains conversation history to resolve pronouns ("his transactions", "her balance").
- **Strict Read-Only Database Boundary**: All database access is funneled through MCP tools enforcing parameterized SQL queries.
- **Production-Grade Error Sanitization & Safety**: Internal stack traces, server IPs, file paths, and database connection strings are stripped before reaching the client.
- **Local LLM Execution**: Uses Qwen 3.5 via Ollama for zero third-party data leakage and low-latency inference.

---

## 🏗️ End-to-End Architecture

```
User
  ↓
React Chat Interface
  ↓
Django REST API
  ↓
FinPay AI Agent
  ↓
Qwen 3.5 9B via Ollama
  ↓
Qwen decides which MCP tool(s) are required
  ↓
MCP Server
  ↓
PostgreSQL
  ↓
Financial data returned through MCP
  ↓
Qwen generates the final answer
  ↓
Django → React → User
```

### System Layer Responsibilities

- **React Chat Interface**: Collects the user's natural-language question, maintains session history, and presents formatted responses/tables.
- **Django REST API**: Exposes the application API (`POST /api/chat/`), validates requests, delegates queries to the agent, and sanitizes outgoing errors.
- **FinPay AI Agent**: Manages conversation context, dynamically discovers MCP tools, handles tool call loops, and orchestrates the execution workflow.
- **Qwen 3.5 9B**: Understands the user's question, selects appropriate tools, interprets tool execution results, and generates the final natural-language response.
- **MCP Server**: Provides controlled, structured, read-only access to financial data using parameterized SQL queries.
- **PostgreSQL**: Stores relational financial records across customers, accounts, merchants, and transactions.

---

## 💡 How a Query Works (Step-by-Step Example)

**User Question**: *"What is Arjun Sharma's current account balance?"*

1. **Question Input**: User submits the question via the React UI.
2. **Intent Understanding**: Qwen interprets the user's intent and determines customer details are needed first.
3. **First Tool Execution**: Qwen invokes `search_customers(query="Arjun Sharma")` via MCP to find the customer ID.
4. **Second Tool Execution**: Using the returned customer ID, Qwen invokes `get_account(account_id=...)` to retrieve the account balance.
5. **Data Retrieval**: PostgreSQL returns the account balance (`₹45,000 INR`) through the MCP Server.
6. **Answer Formatting**: Qwen formats a concise, human-readable response maintaining proper currency formatting.
7. **Delivery**: Django sends the sanitized response to React, which displays it to the user.

---

## 🧠 Qwen + Ollama Integration

FinPay utilizes **Qwen 3.5 (9B)** as its core Large Language Model, served locally through **Ollama**:

- **Model Responsibilities**: Qwen is responsible for understanding natural-language financial questions, deciding when MCP tools are needed, selecting the appropriate tool(s), interpreting tool outputs, and generating the final natural-language response.
- **Ollama Serving Layer**: Ollama acts as the local model serving infrastructure, exposing an internal HTTP API (`/api/chat`) for model interaction.
- **HTTP / API Integration**: The AI Agent sends structured HTTP POST requests to Ollama containing OpenAI-compatible tool schemas dynamically converted from MCP tool definitions.
- **Environment Configuration**: Model connection details are strictly loaded from environment variables.

### Safe Setup Example (Placeholders Only)
```env
# Ollama Local Serving Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3.5:9b
OLLAMA_TIMEOUT=120.0
OLLAMA_TEMPERATURE=0.1
```
*(No external API keys or cloud credentials required; model inference runs entirely on local infrastructure).*

---

## 🔒 Why Model Context Protocol (MCP)?

The **Model Context Protocol (MCP)** acts as a strict, secure boundary between the AI Agent and the underlying database:

1. **Database Access Boundary**: The LLM is **never** given direct access to PostgreSQL or permission to execute raw SQL. All access is mediated through explicit, strongly typed MCP tools.
2. **Preventing SQL Injection**: Tools execute pre-compiled, parameterized SQL queries (`$1`, `$2`), completely eliminating SQL injection risks.
3. **Decoupled Architecture**: The agent interacts with tools using standardized protocol abstractions. Adding tools requires no agent code changes.
4. **Read-Only Enforcers**: Tool implementations are strictly query-only (`SELECT`), preventing unauthorized data modifications (`UPDATE`, `DELETE`).

---

## 🛠️ Implemented MCP Read-Only Tools (7 Tools)

| Tool Name | Parameters | Description |
|---|---|---|
| `search_customers` | `query: str` | Case-insensitive search for customers by name or email. |
| `get_account` | `account_id: str` | Retrieves detailed account information by Account ID. |
| `get_customer_transactions` | `customer_id: str, limit: int = 10` | Fetches recent transactions associated with a customer ID. |
| `get_transaction` | `transaction_id: str` | Fetches details for a specific transaction ID. |
| `search_merchants` | `query: str` | Case-insensitive search for merchants by name or category. |
| `get_merchant_transactions` | `merchant_id: str, limit: int = 10` | Retrieves recent transactions for a specific merchant. |
| `get_transaction_summary` | `customer_id: str` | Calculates aggregate metrics (total spent, count, average) for a customer. |

---

## 🗄️ Database Schema & Relationships

PostgreSQL manages four relational core entities:

```
[ customers ] 1 ─── N [ accounts ] 1 ─── N [ transactions ] N ─── 1 [ merchants ]
```

- **`customers`**: `customer_id` (PK), `first_name`, `last_name`, `email`, `phone`, `created_at`.
- **`accounts`**: `account_id` (PK), `customer_id` (FK), `account_type`, `balance`, `currency`, `status`, `created_at`.
- **`merchants`**: `merchant_id` (PK), `name`, `category`, `created_at`.
- **`transactions`**: `transaction_id` (PK), `account_id` (FK), `merchant_id` (FK), `amount`, `currency`, `transaction_type`, `status`, `created_at`.

---

## ⚡ Django REST API & Security Features

- **API Endpoint**: `POST /api/chat/`
- **Input Validation**: Enforces message size limits (`MAX_MESSAGE_LENGTH = 2000`) and history depth (`MAX_HISTORY_ITEMS = 20`).
- **Error Sanitization**: Intercepts exceptions and redacts sensitive data (internal file paths, IP addresses, DB connection URIs, stack trace dumps).
- **Structured Error Handling**: Returns clean, user-safe error categories (`boundary`, `quota`, `parameter`, `unhandled`).
- **Timeout Management**: Enforces strict HTTP timeouts (`120.0s`) on LLM requests to prevent worker thread starvation.

---

## 💻 React Chatbot Frontend

- **Fintech Dark Theme**: Clean emerald/teal aesthetic with responsive chat layout.
- **Context-Aware History**: Sends clean history payloads with each prompt to maintain multi-turn context.
- **Rich Rendering**: Displays formatted Markdown, financial tables, and interactive suggested queries.
- **Resilient UI State**: Displays clear, non-disruptive alerts when backend system errors occur.

---

## 🧪 Testing & Verification

- **Security Audit** (`test_security_audit.py`): Validates SQL injection resistance, oversized payload rejection, and sensitive data redaction.
- **Failure Modes** (`test_failure_modes.py`): Tests model connection timeouts, invalid tool requests, and max iteration limits.
- **Multi-Turn Context** (`test_context.py`): Verifies coreference resolution across conversation turns.
- **Functional Testing** (`test_functional_fixes.py`): Validates merchant searches, numerical precision, and currency formatting (`₹` / INR).
- **Integration Suite** (`test_django_integration.py`): Tests complete API pipeline from request parsing to final JSON response.

---

## 🧰 Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React, Vite, Vanilla CSS, Lucide Icons |
| **Backend API** | Python, Django, Django REST Framework |
| **AI Agent Core** | Custom Async Orchestrator, FastMCP Framework |
| **LLM Inference** | **Qwen 3.5 (9B)** served locally via **Ollama** |
| **Database** | PostgreSQL, `asyncpg` connection pool |

---

## 📁 Project Structure

```
freshbasket-mcp/
├── ai-agent/                     # AI Agent Core & Ollama Client
│   ├── agent.py                  # FinPayAgent multi-tool orchestrator
│   ├── qwen_client.py            # Ollama API client & parameter configuration
│   └── test_*.py                 # Automated test suites
├── backend/                      # Django REST API Backend
│   ├── dashboard/                # API endpoints & serializers
│   └── manage.py
├── frontend/                     # React Frontend Single Page App
│   ├── src/                      # Chat UI components & App.jsx
│   └── package.json
├── mcp-server/                   # Model Context Protocol Server
│   ├── server.py                 # FastMCP server & 7 read-only tools
│   └── config.py                 # Database pool settings
└── README.md
```

---

## ⚙️ Setup & Run Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL
- [Ollama](https://ollama.ai/) installed and running locally with Qwen (`ollama pull qwen3.5:9b`).

### 1. Seed Database
```bash
psql -U postgres -d finpay_db -f mcp-server/schema.sql
```

### 2. Configure Environment
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=finpay_db
DB_USER=postgres
DB_PASSWORD=your_password
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3.5:9b
```

### 3. Start Backend & Frontend
```bash
# Backend (Django)
cd backend && python manage.py runserver 8000

# Frontend (React)
cd frontend && npm run dev
```

---

## 💬 Example Natural-Language Queries

- **Customer Lookup**: *"Find customer Arjun Sharma and show his account balance."*
- **Multi-Turn Context**:
  - *User*: *"What is Arjun Sharma's account details?"*
  - *User*: *"What about his recent transactions?"*
- **Merchant Search**: *"Show me recent transactions made at Amazon India."*
- **Spending Summary**: *"Give me a spending summary for customer CUST-001."*

---

## 🔮 Future Improvements

- **Write Tool Support**: Introduce human-in-the-loop approval workflows for payment or transfer actions.
- **Role-Based Access Control (RBAC)**: Enforce user-level permission scoping on individual MCP tools.
- **Streaming UI Responses**: Add Server-Sent Events (SSE) for real-time token streaming from Qwen to React.
- **Semantic Vector Search**: Integrate vector embeddings for hybrid retrieval across receipts and financial documents.
