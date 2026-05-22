"""
Run with: python seed_demo.py
Creates a demo user with sample transactions and budgets.
"""
import os, sys, django
from decimal import Decimal
from datetime import date, timedelta
import random

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'spems'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spems.settings')
django.setup()

from django.contrib.auth.models import User
from expenses.models import Category, Transaction, Budget

# Create demo user
user, created = User.objects.get_or_create(
    username='demo',
    defaults={'first_name': 'Demo', 'last_name': 'User', 'email': 'demo@spems.local'}
)
if created:
    user.set_password('demo1234')
    user.save()
    print('Created user: demo / demo1234')
else:
    print('User demo already exists')

# Seed default categories
defaults = [
    ('Food', '🍔', '#ff6b6b'), ('Transport', '🚗', '#4ecdc4'),
    ('Rent', '🏠', '#45b7d1'), ('Entertainment', '🎬', '#f9ca24'),
    ('Healthcare', '💊', '#6c5ce7'), ('Shopping', '🛍️', '#fd79a8'),
    ('Education', '📚', '#00b894'), ('Utilities', '💡', '#fdcb6e'),
    ('Salary', '💼', '#00ff88'), ('Freelance', '💻', '#74b9ff'),
    ('Investment', '📈', '#a29bfe'), ('Other', '📦', '#636e72'),
]
cats = {}
for name, icon, color in defaults:
    cat, _ = Category.objects.get_or_create(user=user, name=name, defaults={'icon': icon, 'color': color})
    cats[name] = cat

today = date.today()

# Sample transactions for last 3 months
sample_expenses = [
    ('Food', 'Grocery shopping', 85.50),
    ('Food', 'Restaurant dinner', 42.00),
    ('Food', 'Coffee & snacks', 18.75),
    ('Transport', 'Uber ride', 12.00),
    ('Transport', 'Monthly bus pass', 55.00),
    ('Entertainment', 'Netflix subscription', 15.99),
    ('Entertainment', 'Cinema tickets', 28.00),
    ('Shopping', 'Amazon order', 67.40),
    ('Utilities', 'Electricity bill', 90.00),
    ('Utilities', 'Internet bill', 45.00),
    ('Healthcare', 'Pharmacy', 32.50),
    ('Education', 'Udemy course', 19.99),
]
sample_income = [
    ('Salary', 'Monthly salary', 3200.00),
    ('Freelance', 'Client project payment', 450.00),
]

Transaction.objects.filter(user=user).delete()

for i in range(3):
    offset_days = i * 30
    for cat_name, desc, amount in sample_expenses:
        Transaction.objects.create(
            user=user, category=cats[cat_name], type='expense',
            description=desc, amount=Decimal(str(amount + random.uniform(-5, 5))),
            date=today - timedelta(days=offset_days + random.randint(0, 25))
        )
    for cat_name, desc, amount in sample_income:
        Transaction.objects.create(
            user=user, category=cats[cat_name], type='income',
            description=desc, amount=Decimal(str(amount)),
            date=today - timedelta(days=offset_days + 1)
        )

print(f'Created {Transaction.objects.filter(user=user).count()} transactions')

# Budgets for current month
Budget.objects.filter(user=user, month=today.month, year=today.year).delete()
budget_limits = [
    ('Food', 300), ('Transport', 100), ('Entertainment', 80),
    ('Shopping', 150), ('Utilities', 150), ('Healthcare', 100),
]
for cat_name, limit in budget_limits:
    Budget.objects.create(
        user=user, category=cats[cat_name],
        amount=Decimal(limit), month=today.month, year=today.year
    )
print(f'Created {len(budget_limits)} budgets')
print('\nDone! Login at http://127.0.0.1:8000/login/')
print('  Username: demo')
print('  Password: demo1234')
