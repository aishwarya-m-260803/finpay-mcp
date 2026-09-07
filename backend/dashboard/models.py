from django.db import models


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.CharField(unique=True, max_length=100)
    phone = models.CharField(max_length=15)
    city = models.CharField(max_length=50)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'customers'

    def __str__(self):
        return f"{self.name} ({self.email})"


class Account(models.Model):
    account_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING)
    account_type = models.CharField(max_length=20)
    balance = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=10)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'accounts'

    def __str__(self):
        return f"Account #{self.account_id} - {self.account_type} ({self.customer.name})"


class Merchant(models.Model):
    merchant_id = models.AutoField(primary_key=True)
    merchant_name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    city = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'merchants'

    def __str__(self):
        return f"{self.merchant_name} ({self.category})"


class Transaction(models.Model):
    transaction_id = models.AutoField(primary_key=True)
    account = models.ForeignKey(Account, on_delete=models.DO_NOTHING)
    merchant = models.ForeignKey(Merchant, on_delete=models.DO_NOTHING, blank=True, null=True)
    transaction_type = models.CharField(max_length=10)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=10)
    transaction_date = models.DateTimeField()
    description = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'transactions'

    def __str__(self):
        return f"Txn #{self.transaction_id} - {self.transaction_type} {self.amount} {self.currency}"
