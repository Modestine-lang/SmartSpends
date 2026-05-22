from django.urls import path
from . import views

urlpatterns = [
    # Landing / root
    path('', views.landing, name='home'),

    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Transactions
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/add/', views.transaction_add, name='transaction_add'),
    path('transactions/<int:pk>/edit/', views.transaction_edit, name='transaction_edit'),
    path('transactions/<int:pk>/delete/', views.transaction_delete, name='transaction_delete'),

    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_add, name='category_add'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Budgets
    path('budgets/', views.budget_list, name='budget_list'),
    path('budgets/add/', views.budget_add, name='budget_add'),
    path('budgets/<int:pk>/edit/', views.budget_edit, name='budget_edit'),
    path('budgets/<int:pk>/delete/', views.budget_delete, name='budget_delete'),

    # Reports
    path('reports/', views.reports, name='reports'),
    path('reports/export/csv/', views.export_report_csv, name='export_csv'),
    path('reports/export/pdf/', views.export_report_pdf, name='export_pdf'),

    # Settings
    path('settings/', views.settings_view, name='settings'),

    # REST API
    path('api/transactions/', views.api_transactions, name='api_transactions'),
    path('api/transactions/<int:pk>/', views.api_transaction_detail, name='api_transaction_detail'),
    path('api/summary/', views.api_summary, name='api_summary'),
]
