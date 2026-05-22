from rest_framework import serializers
from .models import Transaction, Category, Budget


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'icon', 'color', 'is_custom']
        read_only_fields = ['id']


class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Transaction
        fields = ['id', 'amount', 'type', 'description', 'date', 'notes', 'category', 'category_name', 'created_at']
        read_only_fields = ['id', 'created_at']


class BudgetSerializer(serializers.ModelSerializer):
    spent = serializers.SerializerMethodField()
    remaining = serializers.SerializerMethodField()
    percentage = serializers.SerializerMethodField()

    class Meta:
        model = Budget
        fields = ['id', 'category', 'amount', 'month', 'year', 'spent', 'remaining', 'percentage']
        read_only_fields = ['id']

    def get_spent(self, obj):
        return float(obj.spent())

    def get_remaining(self, obj):
        return float(obj.remaining())

    def get_percentage(self, obj):
        return obj.percentage()
