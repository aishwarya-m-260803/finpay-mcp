from django.shortcuts import render
from .models import Account, Customer, Transaction


def home(request):
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
            balance = primary_account.balance
            account_id = primary_account.account_id
            account_type = primary_account.account_type.capitalize()
            account_status = primary_account.status.capitalize()

    context = {
        'customer_name': customer_name,
        'balance': balance,
        'account_id': account_id,
        'account_type': account_type,
        'account_status': account_status,
        'total_customers': total_customers,
        'total_accounts': total_accounts,
        'total_transactions': total_transactions,
    }
    return render(request, 'dashboard/home.html', context)
