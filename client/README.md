# FinPay MCP LLM Client

A Python terminal application that queries the FinPay PostgreSQL database via natural language using the OpenAI API and the Model Context Protocol (MCP).

---

## Features

- **OpenAI Tool Calling**: Uses OpenAI API function calling (`gpt-4o` by default) to reason over user prompts.
- **Dynamic Tool Discovery**: Automatically discovers the 6 MCP tools from `mcp-server/server.py` at runtime.
- **Stdio Connection**: Spawns and communicates with `mcp-server/server.py` via MCP stdio transport.
- **Dual Operating Modes**: Supports single command-line query execution and interactive terminal mode.

---

## Setup Instructions

### 1. Install Dependencies

```bash
cd client
pip install -r requirements.txt
```

### 2. Configure Environment

Create `client/.env` (or copy `.env.example`):

```bash
cp client/.env.example client/.env
```

Set your OpenAI credentials and database URL in `client/.env`:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/finpay
```

---

## Usage

### Single Query Mode

```bash
python client/main.py "Find transactions for customer named Rahul"
```

### Interactive Terminal Mode

```bash
python client/main.py
```

```text
FinPay AI Terminal Connected. Type 'exit' or 'quit' to end.

Ask FinPay > Show transaction summary for account 1
```
