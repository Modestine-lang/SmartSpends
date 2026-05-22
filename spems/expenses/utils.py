import csv
from io import BytesIO
from django.http import HttpResponse
from django.utils import timezone
from .models import Category, Budget
from django.db.models import Sum

# Keyword → category name mapping for auto-categorization
KEYWORD_MAP = {
    'Food': ['restaurant', 'food', 'lunch', 'dinner', 'breakfast', 'cafe', 'coffee', 'pizza', 'burger', 'grocery', 'supermarket', 'eat'],
    'Transport': ['uber', 'taxi', 'bus', 'train', 'fuel', 'petrol', 'gas', 'transport', 'metro', 'fare', 'lyft', 'bolt'],
    'Rent': ['rent', 'lease', 'landlord', 'housing', 'apartment', 'mortgage'],
    'Entertainment': ['netflix', 'spotify', 'cinema', 'movie', 'game', 'concert', 'ticket', 'entertainment', 'youtube', 'subscription'],
    'Healthcare': ['doctor', 'hospital', 'pharmacy', 'medicine', 'clinic', 'health', 'dental', 'medical'],
    'Shopping': ['amazon', 'shop', 'store', 'mall', 'clothes', 'shoes', 'fashion', 'online'],
    'Education': ['school', 'university', 'course', 'book', 'tuition', 'education', 'training', 'udemy'],
    'Utilities': ['electricity', 'water', 'internet', 'phone', 'bill', 'utility', 'wifi', 'mobile'],
    'Salary': ['salary', 'paycheck', 'wage', 'payroll'],
    'Freelance': ['freelance', 'client', 'project', 'invoice', 'contract'],
    'Investment': ['investment', 'dividend', 'stock', 'crypto', 'interest', 'return'],
}


def auto_categorize(user, description):
    """Return a Category based on keyword matching in description."""
    desc_lower = description.lower()
    for cat_name, keywords in KEYWORD_MAP.items():
        if any(kw in desc_lower for kw in keywords):
            cat = Category.objects.filter(user=user, name=cat_name).first()
            if cat:
                return cat
    return Category.objects.filter(user=user, name='Other').first()


def get_budget_alerts(user, month, year):
    """Return list of budgets where spending >= 80% of limit."""
    alerts = []
    budgets = Budget.objects.filter(user=user, month=month, year=year).select_related('category')
    for b in budgets:
        pct = b.percentage()
        if pct >= 100:
            alerts.append({'budget': b, 'pct': pct, 'level': 'danger'})
        elif pct >= 80:
            alerts.append({'budget': b, 'pct': pct, 'level': 'warning'})
    return alerts


def export_csv(queryset, filename, currency='FCFA'):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(['Date', 'Type', 'Category', 'Description', f'Amount ({currency})', 'Notes'])
    for tx in queryset.select_related('category'):
        writer.writerow([
            tx.date, tx.type,
            tx.category.name if tx.category else '',
            tx.description, tx.amount, tx.notes
        ])
    return response


def export_pdf(queryset, user, month, year, currency='FCFA'):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        import calendar

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph(f'SmartSpend Report — {calendar.month_name[month]} {year}', styles['Title']))
        elements.append(Paragraph(f'User: {user.get_full_name() or user.username} | Currency: {currency}', styles['Normal']))
        elements.append(Spacer(1, 20))

        total_income = queryset.filter(type='income').aggregate(t=Sum('amount'))['t'] or 0
        total_expense = queryset.filter(type='expense').aggregate(t=Sum('amount'))['t'] or 0

        summary = [
            ['Total Income', f'{currency} {total_income:,.2f}'],
            ['Total Expense', f'{currency} {total_expense:,.2f}'],
            ['Net Balance', f'{currency} {total_income - total_expense:,.2f}'],
        ]
        t = Table(summary, colWidths=[200, 150])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f5f5f5')),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 20))

        data = [['Date', 'Type', 'Category', 'Description', 'Amount']]
        for tx in queryset.select_related('category').order_by('-date'):
            data.append([
                str(tx.date), tx.type.capitalize(),
                tx.category.name if tx.category else '—',
                tx.description[:40], f'{currency} {tx.amount:,.2f}'
            ])

        table = Table(data, colWidths=[70, 60, 90, 180, 80])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a2540')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="spems_{year}_{month:02d}.pdf"'
        return response
    except ImportError:
        return HttpResponse('ReportLab not installed.', status=500)
