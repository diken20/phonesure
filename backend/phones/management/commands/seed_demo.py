"""Create demo accounts and optional model-reference prices; never create marketplace listings.

Run with: python manage.py seed_demo
"""
from django.core.management.base import BaseCommand

from accounts.models import User
from phones.models import PhoneModelReference

# These are model reference prices for the valuation calculator, not listings for sale.
REFERENCE = [
    ("Apple", "iPhone 11", 64, 52000), ("Apple", "iPhone 12", 128, 70000),
    ("Apple", "iPhone 13", 128, 85000), ("Apple", "iPhone 13", 256, 98000),
    ("Apple", "iPhone 14", 128, 105000), ("Samsung", "Galaxy S21", 128, 75000),
    ("Samsung", "Galaxy S22", 128, 90000), ("Samsung", "Galaxy A52", 128, 42000),
    ("Xiaomi", "Redmi Note 11", 128, 28000), ("Xiaomi", "Redmi Note 12", 128, 32000),
    ("Xiaomi", "Poco X5", 256, 38000), ("OnePlus", "Nord CE 2", 128, 40000),
]


class Command(BaseCommand):
    help = "Create demo users and phone model reference prices; does not create listings"

    def handle(self, *args, **options):
        for brand, model, storage, price in REFERENCE:
            PhoneModelReference.objects.get_or_create(
                brand=brand, model_name=model, storage_gb=storage,
                defaults={"base_price": price},
            )

        for username, role in (("demo_seller", "seller"), ("demo_buyer", "buyer")):
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username, email=f"{username}@example.com",
                    password="demo12345", role=role,
                )

        if not User.objects.filter(username="demo_admin").exists():
            User.objects.create_superuser(
                "demo_admin", "demo_admin@example.com", "demo12345"
            )

        self.stdout.write(self.style.SUCCESS(
            f"{PhoneModelReference.objects.count()} reference prices ready. "
            "No phones/listings were created. Demo logins: demo_seller / demo_buyer / "
            "demo_admin, password demo12345"
        ))
