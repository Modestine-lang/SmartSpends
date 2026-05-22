import os
import sys
from pathlib import Path

# Ensure 'expenses' app is importable when running via gunicorn
sys.path.insert(0, str(Path(__file__).resolve().parent))

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spems.settings')

application = get_wsgi_application()
