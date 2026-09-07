from rest_framework import serializers
from .models import Account, Customer, Merchant, Transaction


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['customer_id', 'name', 'email', 'phone', 'city', 'created_at']


class AccountSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)

    class Meta:
        model = Account
        fields = [
            'account_id',
            'customer',
            'customer_name',
            'account_type',
            'balance',
            'currency',
            'status',
            'created_at',
        ]


class MerchantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Merchant
        fields = ['merchant_id', 'merchant_name', 'category', 'city']


class TransactionSerializer(serializers.ModelSerializer):
    merchant_name = serializers.CharField(source='merchant.merchant_name', read_only=True, default=None)
    account_type = serializers.CharField(source='account.account_type', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'transaction_id',
            'account',
            'account_type',
            'merchant',
            'merchant_name',
            'transaction_type',
            'amount',
            'currency',
            'status',
            'transaction_date',
            'description',
        ]
