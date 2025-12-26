import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vikmo.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = os.getenv("DEMO_ADMIN_USERNAME", "demoadmin")
email = os.getenv("DEMO_ADMIN_EMAIL", "demo@local")
password = os.getenv("DEMO_ADMIN_PASSWORD")

if not password:
    raise ValueError("DEMO_ADMIN_PASSWORD not set")

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print("Demo admin created")
else:
    print("Demo admin already exists")

