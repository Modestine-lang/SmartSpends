#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Create superuser if it doesn't exist (runs once, safe to repeat)
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@spems.local', 'Admin@Spems2026')
    print('Superuser created: admin / Admin@Spems2026')
else:
    print('Superuser already exists')
"
