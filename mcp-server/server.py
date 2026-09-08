"""
FinPay MCP Server
─────────────────
A read-only Model Context Protocol server for FinPay
transaction and account data.
"""

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from dotenv import load_dotenv

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    try:
        from mcp.server.mcpserver import FastMCP  # type: ignore
    except ImportError:
        from mcp.server.mcpserver import MCPServer as FastMCP  # type: ignore

from db import check_connection, get_pool

load_dotenv()  # load .env before anything reads DATABASE_URL

mcp = FastMCP("FinPay")


# ── helpers ──────────────────────────────────────────────────


def _serialize(record: Any) -> Any:
    """Convert asyncpg Records, datetimes, Decimals, dicts, or lists to JSON-serialisable Python types."""
    if isinstance(record, (datetime, date)):
        return record.isoformat()
    if isinstance(record, Decimal):
        return float(record)
    if isinstance(record, dict):
        return {k: _serialize(v) for k, v in record.items()}
    if isinstance(record, (list, tuple, set)):
        return [_serialize(v) for v in record]
    if hasattr(record, "items"):
        return {k: _serialize(v) for k, v in record.items()}
    return record


def _serialize_list(records: list[Any]) -> list[Any]:
    """Convert a list of asyncpg Records or dicts to JSON-serialisable Python objects."""
    return [_serialize(r) for r in records]


# ── lifecycle ────────────────────────────────────────────────


@mcp.resource("health://status")
async def health_check() -> str:
    """Database connectivity check.

    Returns JSON with connection status, PostgreSQL version,
    and public table count.
    """
    try:
        info = await check_connection()
        return json.dumps(info, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "detail": str(e)}, indent=2)


# ── tools ────────────────────────────────────────────────────


@mcp.tool()
async def search_customers(query: str) -> list[dict[str, Any]] | dict[str, Any]:
    """Search customers by name, email, or city using partial matching.

    Args:
        query: Search term to match against customer name, email, or city.

    Returns:
        Structured array of matching customer records or message object.
    """
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT customer_id, name, email, phone, city, created_at
                FROM   customers
                WHERE  name  ILIKE $1
                   OR  email ILIKE $1
                   OR  city  ILIKE $1
                ORDER BY customer_id
                """,
                f"%{query}%",
            )
        if not rows:
            return {"message": f"No customers matching '{query}'", "customers": []}
        return _serialize_list(rows)
    except Exception as e:
        return {"error": f"Database query failed: {str(e)}"}


@mcp.tool()
async def get_account(account_id: int) -> dict[str, Any]:
    """Get account details by ID, including the owning customer's info.

    Args:
        account_id: The unique account identifier.

    Returns:
        Structured object with account and customer details or error message.
    """
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT a.account_id,
                       a.account_type,
                       a.balance,
                       a.currency,
                       a.status,
                       a.created_at,
                       c.customer_id,
                       c.name  AS customer_name,
                       c.email AS customer_email,
                       c.phone AS customer_phone,
                       c.city  AS customer_city
                FROM   accounts  a
                JOIN   customers c USING (customer_id)
                WHERE  a.account_id = $1
                """,
                account_id,
            )

        if row is None:
            return {"error": f"Account {account_id} not found"}

        return _serialize(row)
    except Exception as e:
        return {"error": f"Database query failed: {str(e)}"}


@mcp.tool()
async def get_customer_transactions(
    customer_id: int, limit: int = 50
) -> list[dict[str, Any]] | dict[str, Any]:
    """Get all transactions across all accounts belonging to a customer.

    Args:
        customer_id: The unique customer identifier.
        limit: Maximum number of transactions to return (default 50).

    Returns:
        Structured array of transaction records ordered by date descending.
    """
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT t.transaction_id,
                       t.account_id,
                       a.account_type,
                       t.merchant_id,
                       m.merchant_name,
                       t.transaction_type,
                       t.amount,
                       t.currency,
                       t.status,
                       t.transaction_date,
                       t.description
                FROM   transactions t
                JOIN   accounts  a ON a.account_id  = t.account_id
                LEFT JOIN merchants m ON m.merchant_id = t.merchant_id
                WHERE  a.customer_id = $1
                ORDER  BY t.transaction_date DESC
                LIMIT  $2
                """,
                customer_id,
                limit,
            )
        if not rows:
            return {"message": f"No transactions found for customer {customer_id}", "transactions": []}
        return _serialize_list(rows)
    except Exception as e:
        return {"error": f"Database query failed: {str(e)}"}


@mcp.tool()
async def get_transaction(transaction_id: int) -> dict[str, Any]:
    """Get complete details of a single transaction including account, customer, and merchant info.

    Args:
        transaction_id: The unique transaction identifier.

    Returns:
        Structured object with full transaction details or error message.
    """
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT t.transaction_id,
                       t.account_id,
                       a.account_type,
                       a.balance AS account_balance,
                       c.customer_id,
                       c.name  AS customer_name,
                       c.email AS customer_email,
                       t.merchant_id,
                       m.merchant_name,
                       m.category AS merchant_category,
                       t.transaction_type,
                       t.amount,
                       t.currency,
                       t.status,
                       t.transaction_date,
                       t.description
                FROM   transactions t
                JOIN   accounts  a ON a.account_id  = t.account_id
                JOIN   customers c ON c.customer_id = a.customer_id
                LEFT JOIN merchants m ON m.merchant_id = t.merchant_id
                WHERE  t.transaction_id = $1
                """,
                transaction_id,
            )
        if row is None:
            return {"error": f"Transaction {transaction_id} not found"}
        return _serialize(row)
    except Exception as e:
        return {"error": f"Database query failed: {str(e)}"}


@mcp.tool()
async def search_merchants(query: str) -> list[dict[str, Any]] | dict[str, Any]:
    """Search merchants by merchant name or category using partial matching.

    Args:
        query: Search term to match against merchant_name or category.

    Returns:
        Structured array of matching merchant records or message object.
    """
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT merchant_id, merchant_name, category, city
                FROM   merchants
                WHERE  merchant_name ILIKE $1
                   OR  category      ILIKE $1
                ORDER BY merchant_id
                """,
                f"%{query}%",
            )
        if not rows:
            return {"message": f"No merchants matching '{query}'", "merchants": []}
        return _serialize_list(rows)
    except Exception as e:
        return {"error": f"Database query failed: {str(e)}"}


@mcp.tool()
async def get_merchant_transactions(
    merchant_id: int, limit: int = 50
) -> list[dict[str, Any]] | dict[str, Any]:
    """Get all transactions for a specific merchant.

    Args:
        merchant_id: The unique merchant identifier.
        limit: Maximum number of transactions to return (default 50).

    Returns:
        Structured array of transaction records ordered by date descending.
    """
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT t.transaction_id,
                       t.account_id,
                       a.account_type,
                       c.customer_id,
                       c.name AS customer_name,
                       m.merchant_name,
                       m.category AS merchant_category,
                       t.transaction_type,
                       t.amount,
                       t.currency,
                       t.status,
                       t.transaction_date,
                       t.description
                FROM   transactions t
                JOIN   accounts  a ON a.account_id  = t.account_id
                JOIN   customers c ON c.customer_id = a.customer_id
                JOIN   merchants m ON m.merchant_id = t.merchant_id
                WHERE  t.merchant_id = $1
                ORDER  BY t.transaction_date DESC
                LIMIT  $2
                """,
                merchant_id,
                limit,
            )
        if not rows:
            return {"message": f"No transactions found for merchant {merchant_id}", "transactions": []}
        return _serialize_list(rows)
    except Exception as e:
        return {"error": f"Database query failed: {str(e)}"}


@mcp.tool()
async def get_transaction_summary(
    account_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict[str, Any]:
    """Return transaction count, total amount, and average amount grouped by transaction type for an account.

    Args:
        account_id: The unique account identifier.
        start_date: Optional inclusive start date (YYYY-MM-DD format).
        end_date: Optional inclusive end date (YYYY-MM-DD format).

    Returns:
        Structured object with aggregate stats grouped by transaction type and overall summary.
    """
    try:
        pool = await get_pool()

        params: list[Any] = [account_id]
        where_clauses = ["t.account_id = $1", "t.status = 'success'"]

        if start_date:
            params.append(start_date)
            where_clauses.append(f"t.transaction_date >= ${len(params)}::timestamptz")
        if end_date:
            params.append(end_date)
            where_clauses.append(f"t.transaction_date < (${len(params)}::date + 1)::timestamptz")

        where_sql = " AND ".join(where_clauses)
        query = f"""
            SELECT t.transaction_type,
                   COUNT(*)::int              AS transaction_count,
                   SUM(t.amount)              AS total_amount,
                   ROUND(AVG(t.amount), 2)    AS average_amount
            FROM   transactions t
            WHERE  {where_sql}
            GROUP  BY t.transaction_type
            ORDER  BY t.transaction_type
        """

        async with pool.acquire() as conn:
            acc_row = await conn.fetchrow("SELECT currency FROM accounts WHERE account_id = $1", account_id)
            curr = acc_row["currency"] if acc_row and "currency" in acc_row else "INR"
            rows = await conn.fetch(query, *params)

        if not rows:
            return {
                "account_id": account_id,
                "currency": curr,
                "date_range": {"start_date": start_date, "end_date": end_date},
                "message": "No successful transactions found for the specified criteria",
                "by_transaction_type": [],
            }

        breakdown = _serialize_list(rows)
        total_count = sum(r["transaction_count"] for r in breakdown)
        total_sum = round(sum(r["total_amount"] for r in breakdown), 2)
        overall_avg = round(total_sum / total_count, 2) if total_count > 0 else 0.0

        return {
            "account_id": account_id,
            "currency": curr,
            "date_range": {"start_date": start_date, "end_date": end_date},
            "overall_summary": {
                "currency": curr,
                "total_transactions": total_count,
                "total_amount": total_sum,
                "average_amount": overall_avg,
            },
            "by_transaction_type": breakdown,
        }
    except Exception as e:
        return {"error": f"Database query failed: {str(e)}"}



# ── entry point ──────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
