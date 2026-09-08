import sys
from pathlib import Path

from asgiref.sync import async_to_sync
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Account, Customer, Transaction
from .serializers import AccountSerializer, CustomerSerializer, TransactionSerializer


@api_view(['GET'])
def api_dashboard_summary(request):
    """GET /api/dashboard/ -> summary counts & Arjun Sharma balance."""
    total_customers = Customer.objects.count()
    total_accounts = Account.objects.count()
    total_transactions = Transaction.objects.count()

    customer_name = "Arjun Sharma"
    balance = 0.0
    account_id = None
    account_type = "Savings"
    account_status = "Active"

    arjun = Customer.objects.filter(name="Arjun Sharma").first()
    if arjun:
        customer_name = arjun.name
        primary_account = Account.objects.filter(customer=arjun).first()
        if primary_account:
            balance = float(primary_account.balance)
            account_id = primary_account.account_id
            account_type = primary_account.account_type.capitalize()
            account_status = primary_account.status.capitalize()

    data = {
        'customer_name': customer_name,
        'balance': balance,
        'account_id': account_id,
        'account_type': account_type,
        'account_status': account_status,
        'total_customers': total_customers,
        'total_accounts': total_accounts,
        'total_transactions': total_transactions,
    }
    return Response(data)


@api_view(['GET'])
def api_customer_list(request):
    """GET /api/customers/ -> list all customers."""
    customers = Customer.objects.all().order_by('customer_id')
    serializer = CustomerSerializer(customers, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def api_account_list(request):
    """GET /api/accounts/ -> list all accounts."""
    accounts = Account.objects.select_related('customer').all().order_by('account_id')
    serializer = AccountSerializer(accounts, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def api_transaction_list(request):
    """GET /api/transactions/ -> list recent transactions."""
    transactions = Transaction.objects.select_related('account', 'merchant').all().order_by('-transaction_date')[:50]
    serializer = TransactionSerializer(transactions, many=True)
    return Response(serializer.data)


def _sanitize_error(error_msg: str) -> str:
    """Strip API keys and secrets from error messages."""
    import re
    return re.sub(
        r'(?:AQ\.[A-Za-z0-9_\-]+|AIza[0-9A-Za-z-_]{35}|sk-[A-Za-z0-9]{32,})',
        '[REDACTED]',
        error_msg,
    )


def _classify_error(sanitized_msg: str) -> tuple[str, str]:
    """
    Classify a sanitized error string into one of four structured categories.

    Returns (category, user_facing_message).
    Categories:
        1. quota       — API Quota or Key Exhaustion (429, rate limit, auth)
        2. boundary    — MCP Boundary & Rule Violations (cross-tenant, restricted)
        3. parameter   — Parameter Mismatch / Missing Filter
        4. unhandled   — Unhandled Tool Exception (fallback)
    """
    msg_lower = sanitized_msg.lower()

    # ── Category 1: API Quota or Key Exhaustion ──────────────
    quota_keywords = [
        "429", "resource_exhausted", "quota", "rate limit", "rate_limit",
        "insufficient_quota", "limit exceeded", "limitexceeded",
        "billing", "api key", "api_key", "invalid key", "invalid_key",
        "authentication", "auth failure", "unauthorized", "forbidden",
        "permission denied", "access denied",
    ]
    if any(kw in msg_lower for kw in quota_keywords):
        return (
            "quota",
            "**Service Alert:** The request cannot be completed because the API quota "
            "or access key has been exhausted. Please check your API credits or "
            "credentials to restore service.",
        )

    # ── Category 2: MCP Boundary & Rule Violations ───────────
    boundary_keywords = [
        "cross-tenant", "cross_tenant", "tenant mismatch",
        "unauthorized data", "restricted", "not permitted",
        "boundary", "scope violation", "access violation",
        "customer id mismatch", "session mismatch",
        "write operation", "delete operation", "alter table",
        "drop table", "create table", "truncate",
    ]
    if any(kw in msg_lower for kw in boundary_keywords):
        # Extract a specific reason fragment when possible
        reason = "Operation falls outside the permitted MCP scope."
        if "cross-tenant" in msg_lower or "cross_tenant" in msg_lower:
            reason = "Cross-tenant querying is restricted."
        elif "customer id mismatch" in msg_lower:
            reason = "Customer ID mismatch — you may only access your own records."
        elif any(op in msg_lower for op in ["write operation", "delete operation", "alter table", "drop table", "create table", "truncate"]):
            reason = "Schema-modifying and write operations are not permitted on this read-only system."
        elif "restricted" in msg_lower:
            reason = "The requested action is restricted by system policy."

        return (
            "boundary",
            f"**Boundary Notice:** This request falls outside the permitted operational "
            f"boundaries of this system.\n"
            f"- **Reason:** {reason}\n"
            f"- **Permitted Scope:** You can only query records associated with your active session.",
        )

    # ── Category 3: Parameter Mismatch / Missing Filter ──────
    param_keywords = [
        "missing", "required", "invalid parameter", "invalid_parameter",
        "missing filter", "column", "does not exist", "type error",
        "typeerror", "valueerror", "not found", "no such",
        "invalid input", "invalid_input", "malformed",
        "expected", "argument", "field required",
    ]
    if any(kw in msg_lower for kw in param_keywords):
        return (
            "parameter",
            f"**Query Execution Notice:** The request could not be fulfilled due to "
            f"missing or invalid parameters. {sanitized_msg}",
        )

    # ── Category 4: Unhandled Tool Exception (fallback) ──────
    return (
        "unhandled",
        f"**Technical Fault:** The query failed to execute due to an internal "
        f"server error: {sanitized_msg}",
    )


def _unwrap_exception_group(exc: BaseException) -> BaseException:
    """Recursively unwrap ExceptionGroup / BaseExceptionGroup to the real root cause.

    The MCP SDK's stdio_client uses an asyncio.TaskGroup internally.
    When any exception escapes the ``async with mcp_client.connect():``
    block, the TaskGroup wraps it in an ExceptionGroup with the opaque
    message "unhandled errors in a TaskGroup (1 sub-exception)".

    This helper peels that wrapper off (potentially multiple layers)
    and returns the actual sub-exception so the error classifier can
    inspect the real error string.
    """
    # Python 3.11+ ExceptionGroup inherits from BaseException
    while True:
        if isinstance(exc, BaseExceptionGroup):
            # Pick the first sub-exception (there's almost always just one)
            sub_exceptions = exc.exceptions
            if sub_exceptions:
                exc = sub_exceptions[0]
                continue
        # Also handle the older-style __cause__ / __context__ chains
        # in case the group itself wraps via `raise ... from ...`
        break
    return exc


@api_view(['POST'])
def api_chat(request):
    """POST /api/chat/ -> delegates to ai-agent (Qwen + MCP), returns {"response": "<final AI answer>"}."""
    message = request.data.get('message') if isinstance(request.data, dict) else None
    if not message or not str(message).strip():
        return Response(
            {
                'success': False,
                'error_type': 'ValidationError',
                'message': 'A non-empty "message" field is required.',
                'details': 'The request body must contain a "message" field with a non-empty string value.',
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    clean_message = str(message).strip()

    try:
        # Ensure project root and ai-agent dir are in sys.path
        project_root = Path(settings.BASE_DIR).parent
        ai_agent_dir = project_root / "ai-agent"
        for p in [str(project_root), str(ai_agent_dir)]:
            if p not in sys.path:
                sys.path.insert(0, p)

        from agent import FinPayAgent

        async def _execute_agent_query(prompt: str) -> str:
            """Delegate to FinPayAgent — all AI + MCP logic lives in ai-agent/."""
            agent = FinPayAgent()
            try:
                return await agent.run_with_mcp(prompt)
            except BaseException as inner_exc:
                # Unwrap ExceptionGroup *inside* the async function
                # so we re-raise the real root cause as a plain Exception
                root = _unwrap_exception_group(inner_exc)
                if root is not inner_exc:
                    raise type(root)(str(root)) from root
                raise

        ai_response = async_to_sync(_execute_agent_query)(clean_message)
        return Response({'success': True, 'response': ai_response})

    except BaseException as e:
        # ── Step 1: Unwrap ExceptionGroup if present ──────────
        root_exc = _unwrap_exception_group(e)
        raw_error_msg = str(root_exc)
        error_type_name = type(root_exc).__name__

        # ── Step 2: Sanitize secrets from error string ────────
        sanitized_msg = _sanitize_error(raw_error_msg)

        # ── Step 3: Classify via typed exceptions first ───────
        category = None
        user_msg = None
        try:
            from client.llm_runner import (
                MCPBoundaryError,
                MCPParameterError,
                MCPQuotaError,
                MCPToolError,
            )
            exc_type_map = {
                MCPQuotaError: 'quota',
                MCPBoundaryError: 'boundary',
                MCPParameterError: 'parameter',
                MCPToolError: 'unhandled',
            }
            for exc_cls, cat in exc_type_map.items():
                if isinstance(root_exc, exc_cls):
                    category = cat
                    _, user_msg = _classify_error(sanitized_msg)
                    break
        except ImportError:
            pass

        # ── Step 4: Fall through to keyword classifier ────────
        if category is None:
            category, user_msg = _classify_error(sanitized_msg)

        # ── Step 5: Map to HTTP status codes ──────────────────
        status_code_map = {
            'quota': status.HTTP_429_TOO_MANY_REQUESTS,
            'boundary': status.HTTP_403_FORBIDDEN,
            'parameter': status.HTTP_400_BAD_REQUEST,
            'unhandled': status.HTTP_500_INTERNAL_SERVER_ERROR,
        }

        return Response(
            {
                'success': False,
                'error_type': error_type_name,
                'message': user_msg,
                'details': sanitized_msg,
                'category': category,
            },
            status=status_code_map.get(category, status.HTTP_500_INTERNAL_SERVER_ERROR),
        )

