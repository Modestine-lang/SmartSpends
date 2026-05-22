from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Transaction, Category, Budget, UserProfile
from .forms import RegisterForm, LoginForm, TransactionForm, CategoryForm, BudgetForm, CurrencyForm
from .serializers import TransactionSerializer, CategorySerializer, BudgetSerializer
from .utils import auto_categorize, get_budget_alerts, export_csv, export_pdf
import json
from datetime import date, timedelta
import calendar


# ── Auth ──────────────────────────────────────────────────────────────────────

def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        _seed_default_categories(user)
        UserProfile.objects.get_or_create(user=user)
        login(request, user)
        messages.success(request, 'Welcome to SmartSpend!')
        return redirect('dashboard')
    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect(request.GET.get('next', 'dashboard'))
    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# ── Dashboard ─────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    today = date.today()
    month, year = today.month, today.year

    txs = Transaction.objects.filter(user=request.user)
    month_txs = txs.filter(date__month=month, date__year=year)

    total_income = month_txs.filter(type='income').aggregate(t=Sum('amount'))['t'] or 0
    total_expense = month_txs.filter(type='expense').aggregate(t=Sum('amount'))['t'] or 0
    balance = total_income - total_expense

    recent = txs[:8]
    budgets = Budget.objects.filter(user=request.user, month=month, year=year).select_related('category')
    alerts = get_budget_alerts(request.user, month, year)

    # Chart data: last 6 months
    chart_labels, chart_income, chart_expense = [], [], []
    for i in range(5, -1, -1):
        d = today.replace(day=1) - timedelta(days=i * 28)
        m, y = d.month, d.year
        chart_labels.append(calendar.month_abbr[m])
        chart_income.append(float(txs.filter(type='income', date__month=m, date__year=y)
                                  .aggregate(t=Sum('amount'))['t'] or 0))
        chart_expense.append(float(txs.filter(type='expense', date__month=m, date__year=y)
                                   .aggregate(t=Sum('amount'))['t'] or 0))

    # Category breakdown for pie chart
    cat_data = month_txs.filter(type='expense').values('category__name', 'category__color') \
        .annotate(total=Sum('amount')).order_by('-total')[:6]

    ctx = {
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
        'recent': recent,
        'budgets': budgets,
        'alerts': alerts,
        'chart_labels': json.dumps(chart_labels),
        'chart_income': json.dumps(chart_income),
        'chart_expense': json.dumps(chart_expense),
        'cat_labels': json.dumps([c['category__name'] or 'Uncategorized' for c in cat_data]),
        'cat_values': json.dumps([float(c['total']) for c in cat_data]),
        'cat_colors': json.dumps([c['category__color'] or '#00ff88' for c in cat_data]),
        'month_name': calendar.month_name[month],
        'year': year,
    }
    return render(request, 'dashboard.html', ctx)


# ── Transactions ──────────────────────────────────────────────────────────────

@login_required
def transaction_list(request):
    txs = Transaction.objects.filter(user=request.user).select_related('category')

    # Filters
    tx_type = request.GET.get('type', '')
    category_id = request.GET.get('category', '')
    month = request.GET.get('month', '')
    year = request.GET.get('year', '')
    search = request.GET.get('q', '')

    if tx_type:
        txs = txs.filter(type=tx_type)
    if category_id:
        txs = txs.filter(category_id=category_id)
    if month:
        txs = txs.filter(date__month=month)
    if year:
        txs = txs.filter(date__year=year)
    if search:
        txs = txs.filter(Q(description__icontains=search) | Q(notes__icontains=search))

    categories = Category.objects.filter(user=request.user)
    ctx = {
        'transactions': txs,
        'categories': categories,
        'filters': {'type': tx_type, 'category': category_id, 'month': month, 'year': year, 'q': search},
        'years': range(2020, date.today().year + 1),
    }
    return render(request, 'transactions/list.html', ctx)


@login_required
def transaction_add(request):
    form = TransactionForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        tx = form.save(commit=False)
        tx.user = request.user
        # Auto-categorize if no category chosen
        if not tx.category:
            tx.category = auto_categorize(request.user, tx.description)
        tx.save()
        messages.success(request, 'Transaction added.')
        return redirect('transaction_list')
    return render(request, 'transactions/form.html', {'form': form, 'title': 'Add Transaction'})


@login_required
def transaction_edit(request, pk):
    tx = get_object_or_404(Transaction, pk=pk, user=request.user)
    form = TransactionForm(request.user, request.POST or None, instance=tx)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Transaction updated.')
        return redirect('transaction_list')
    return render(request, 'transactions/form.html', {'form': form, 'title': 'Edit Transaction', 'tx': tx})


@login_required
def transaction_delete(request, pk):
    tx = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        tx.delete()
        messages.success(request, 'Transaction deleted.')
        return redirect('transaction_list')
    return render(request, 'transactions/confirm_delete.html', {'obj': tx, 'type': 'transaction'})


# ── Categories ────────────────────────────────────────────────────────────────

@login_required
def category_list(request):
    cats = Category.objects.filter(user=request.user).annotate(tx_count=Count('transactions'))
    return render(request, 'categories/list.html', {'categories': cats})


@login_required
def category_add(request):
    form = CategoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cat = form.save(commit=False)
        cat.user = request.user
        cat.is_custom = True
        cat.save()
        messages.success(request, 'Category created.')
        return redirect('category_list')
    return render(request, 'categories/form.html', {'form': form, 'title': 'Add Category'})


@login_required
def category_edit(request, pk):
    cat = get_object_or_404(Category, pk=pk, user=request.user)
    form = CategoryForm(request.POST or None, instance=cat)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category updated.')
        return redirect('category_list')
    return render(request, 'categories/form.html', {'form': form, 'title': 'Edit Category', 'cat': cat})


@login_required
def category_delete(request, pk):
    cat = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        cat.delete()
        messages.success(request, 'Category deleted.')
        return redirect('category_list')
    return render(request, 'transactions/confirm_delete.html', {'obj': cat, 'type': 'category'})


# ── Budgets ───────────────────────────────────────────────────────────────────

@login_required
def budget_list(request):
    today = date.today()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))
    budgets = Budget.objects.filter(user=request.user, month=month, year=year).select_related('category')
    ctx = {
        'budgets': budgets,
        'month': month,
        'year': year,
        'month_name': calendar.month_name[month],
        'years': range(2020, today.year + 2),
    }
    return render(request, 'budgets/list.html', ctx)


@login_required
def budget_add(request):
    today = date.today()
    form = BudgetForm(request.user, request.POST or None,
                      initial={'month': today.month, 'year': today.year})
    if request.method == 'POST' and form.is_valid():
        budget = form.save(commit=False)
        budget.user = request.user
        budget.save()
        messages.success(request, 'Budget set.')
        return redirect('budget_list')
    return render(request, 'budgets/form.html', {'form': form, 'title': 'Set Budget'})


@login_required
def budget_edit(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    form = BudgetForm(request.user, request.POST or None, instance=budget)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Budget updated.')
        return redirect('budget_list')
    return render(request, 'budgets/form.html', {'form': form, 'title': 'Edit Budget', 'budget': budget})


@login_required
def budget_delete(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    if request.method == 'POST':
        budget.delete()
        messages.success(request, 'Budget removed.')
        return redirect('budget_list')
    return render(request, 'transactions/confirm_delete.html', {'obj': budget, 'type': 'budget'})


# ── Reports ───────────────────────────────────────────────────────────────────

@login_required
def reports(request):
    today = date.today()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))

    txs = Transaction.objects.filter(user=request.user, date__month=month, date__year=year)
    total_income = txs.filter(type='income').aggregate(t=Sum('amount'))['t'] or 0
    total_expense = txs.filter(type='expense').aggregate(t=Sum('amount'))['t'] or 0

    by_category = txs.filter(type='expense').values('category__name', 'category__color') \
        .annotate(total=Sum('amount'), count=Count('id')).order_by('-total')

    # Weekly trend
    weekly = []
    for week in range(4):
        start = date(year, month, 1) + timedelta(weeks=week)
        end = start + timedelta(days=6)
        w_exp = txs.filter(type='expense', date__gte=start, date__lte=end) \
            .aggregate(t=Sum('amount'))['t'] or 0
        weekly.append(float(w_exp))

    ctx = {
        'month': month,
        'year': year,
        'month_name': calendar.month_name[month],
        'total_income': total_income,
        'total_expense': total_expense,
        'net': total_income - total_expense,
        'by_category': by_category,
        'cat_labels': json.dumps([c['category__name'] or 'Uncategorized' for c in by_category]),
        'cat_values': json.dumps([float(c['total']) for c in by_category]),
        'cat_colors': json.dumps([c['category__color'] or '#00ff88' for c in by_category]),
        'weekly_data': json.dumps(weekly),
        'years': range(2020, today.year + 1),
    }
    return render(request, 'reports/index.html', ctx)


@login_required
def export_report_csv(request):
    month = int(request.GET.get('month', date.today().month))
    year = int(request.GET.get('year', date.today().year))
    txs = Transaction.objects.filter(user=request.user, date__month=month, date__year=year)
    currency = getattr(getattr(request.user, 'profile', None), 'currency', 'FCFA')
    return export_csv(txs, f'spems_{year}_{month:02d}.csv', currency)


@login_required
def export_report_pdf(request):
    month = int(request.GET.get('month', date.today().month))
    year = int(request.GET.get('year', date.today().year))
    txs = Transaction.objects.filter(user=request.user, date__month=month, date__year=year)
    currency = getattr(getattr(request.user, 'profile', None), 'currency', 'FCFA')
    return export_pdf(txs, request.user, month, year, currency)


# ── REST API ──────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
def api_transactions(request):
    if request.method == 'GET':
        txs = Transaction.objects.filter(user=request.user)
        return Response(TransactionSerializer(txs, many=True).data)
    serializer = TransactionSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)


@api_view(['GET', 'PUT', 'DELETE'])
def api_transaction_detail(request, pk):
    tx = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'GET':
        return Response(TransactionSerializer(tx).data)
    if request.method == 'PUT':
        s = TransactionSerializer(tx, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=400)
    tx.delete()
    return Response(status=204)


@api_view(['GET'])
def api_summary(request):
    today = date.today()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))
    txs = Transaction.objects.filter(user=request.user, date__month=month, date__year=year)
    income = txs.filter(type='income').aggregate(t=Sum('amount'))['t'] or 0
    expense = txs.filter(type='expense').aggregate(t=Sum('amount'))['t'] or 0
    return Response({'income': income, 'expense': expense, 'balance': income - expense})


# ── Helpers ───────────────────────────────────────────────────────────────────

@login_required
def settings_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    form = CurrencyForm(request.POST or None, instance=profile)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Currency updated to {profile.currency}.')
        return redirect('settings')
    return render(request, 'settings.html', {'form': form, 'profile': profile})



    defaults = [
        ('Food', '🍔', '#ff6b6b'),
        ('Transport', '🚗', '#4ecdc4'),
        ('Rent', '🏠', '#45b7d1'),
        ('Entertainment', '🎬', '#f9ca24'),
        ('Healthcare', '💊', '#6c5ce7'),
        ('Shopping', '🛍️', '#fd79a8'),
        ('Education', '📚', '#00b894'),
        ('Utilities', '💡', '#fdcb6e'),
        ('Salary', '💼', '#00ff88'),
        ('Freelance', '💻', '#74b9ff'),
        ('Investment', '📈', '#a29bfe'),
        ('Other', '📦', '#636e72'),
    ]
    for name, icon, color in defaults:
        Category.objects.get_or_create(user=user, name=name, defaults={'icon': icon, 'color': color})
