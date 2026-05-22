from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


CURRENCY_CHOICES = [
    ('FCFA', 'FCFA — CFA Franc'),
    ('$',    'USD — US Dollar'),
    ('€',    'EUR — Euro'),
    ('£',    'GBP — British Pound'),
    ('₦',    'NGN — Nigerian Naira'),
    ('KSh',  'KES — Kenyan Shilling'),
    ('R',    'ZAR — South African Rand'),
    ('GH₵',  'GHS — Ghanaian Cedi'),
    ('¥',    'JPY — Japanese Yen'),
    ('₹',    'INR — Indian Rupee'),
    ('C$',   'CAD — Canadian Dollar'),
    ('A$',   'AUD — Australian Dollar'),
]


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='FCFA')

    def __str__(self):
        return f'{self.user.username} profile'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()



class Category(models.Model):
    PREDEFINED = [
        ('Food', '🍔 Food'),
        ('Transport', '🚗 Transport'),
        ('Rent', '🏠 Rent'),
        ('Entertainment', '🎬 Entertainment'),
        ('Healthcare', '💊 Healthcare'),
        ('Shopping', '🛍️ Shopping'),
        ('Education', '📚 Education'),
        ('Utilities', '💡 Utilities'),
        ('Salary', '💼 Salary'),
        ('Freelance', '💻 Freelance'),
        ('Investment', '📈 Investment'),
        ('Other', '📦 Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=10, default='📦')
    color = models.CharField(max_length=20, default='#00ff88')
    is_custom = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'name')
        ordering = ['name']

    def __str__(self):
        return self.name


class Transaction(models.Model):
    TYPE_CHOICES = [('income', 'Income'), ('expense', 'Expense')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    description = models.CharField(max_length=255)
    date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.type}: {self.description} ({self.amount})"


class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budgets')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    month = models.IntegerField()  # 1-12
    year = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'category', 'month', 'year')
        ordering = ['-year', '-month']

    def __str__(self):
        return f"{self.category.name} budget {self.month}/{self.year}: {self.amount}"

    def spent(self):
        return self.category.transactions.filter(
            user=self.user,
            type='expense',
            date__month=self.month,
            date__year=self.year
        ).aggregate(total=models.Sum('amount'))['total'] or 0

    def remaining(self):
        return self.amount - self.spent()

    def percentage(self):
        if self.amount == 0:
            return 0
        return min(round((self.spent() / self.amount) * 100, 1), 100)
