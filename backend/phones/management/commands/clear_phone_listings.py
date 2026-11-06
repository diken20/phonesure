"""Delete all phone listings while preserving users and phone model references.

Run: python manage.py clear_phone_listings
"""
from django.core.management.base import BaseCommand
from phones.models import Phone


class Command(BaseCommand):
    help = "Delete every phone listing; preserve users and model reference prices"

    def handle(self, *args, **options):
        count = Phone.objects.count()
        Phone.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(
            f"Deleted {count} phone listing(s). User accounts and model reference prices were kept."
        ))
