from django.contrib import admin
from .models import Category, Transaction, Budget


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'user', 'is_custom', 'created_at']
    list_filter = ['is_custom', 'user']
    search_fields = ['name']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['description', 'type', 'amount', 'category', 'date', 'user']
    list_filter = ['type', 'category', 'date']
    search_fields = ['description', 'notes']
    date_hierarchy = 'date'


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['category', 'amount', 'month', 'year', 'user']
    list_filter = ['month', 'year', 'user']
