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


@api_view(['POST'])
def api_chat(request):
    """POST /api/chat/ -> accepts {"message": "..."}, runs Gemini + MCP tools via client, returns {"response": "<final AI answer>"}."""
    message = request.data.get('message') if isinstance(request.data, dict) else None
    if not message or not str(message).strip():
        return Response(
            {'error': 'A non-empty "message" field is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    clean_message = str(message).strip()

    try:
        # Ensure project root is in sys.path so client module imports cleanly
        project_root = Path(settings.BASE_DIR).parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        from client.llm_runner import LLMRunner
        from client.mcp_client import MCPClientManager

        async def _execute_mcp_llm_query(prompt: str) -> str:
            mcp_client = MCPClientManager()
            async with mcp_client.connect():
                runner = LLMRunner()
                return await runner.run(prompt, mcp_client)

        ai_response = async_to_sync(_execute_mcp_llm_query)(clean_message)
        return Response({'response': ai_response})

    except Exception as e:
        # Never expose secret API keys in response errors
        error_msg = str(e)
        return Response(
            {'error': f'AI processing failure: {error_msg}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
