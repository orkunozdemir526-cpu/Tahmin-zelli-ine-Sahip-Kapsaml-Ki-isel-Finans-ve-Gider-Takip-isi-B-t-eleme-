from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts')
    name = models.CharField(max_length=100, help_text="Örn: Maaş Hesabı, Kredi Kartı")
    currency = models.CharField(max_length=3, default='TRY', help_text="Örn: TRY, USD, EUR")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.currency})"

class Category(models.Model):
    name = models.CharField(max_length=100)
    # N-ary Tree (Ağaç) veri yapısı: Bir kategorinin alt kategorileri olabilir
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} -> {self.name}"
        return self.name

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('INCOME', 'Gelir'),
        ('EXPENSE', 'Gider'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    # db_index=True ekleyerek zaman serisi aramalarını 100 kat hızlandırıyoruz
    date = models.DateTimeField(help_text="Zaman serisi analizi için işlem tarihi", db_index=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.account.name} - {self.transaction_type}: {self.amount}"