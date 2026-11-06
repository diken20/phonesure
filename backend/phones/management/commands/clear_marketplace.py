from django.core.management.base import BaseCommand
from phones.models import Phone

class Command(BaseCommand):
    help = 'Hide all current marketplace listings by moving them back to draft; seller phone details are preserved.'

    def handle(self, *args, **options):
        count = Phone.objects.filter(status=Phone.Status.LISTED).update(status=Phone.Status.DRAFT)
        self.stdout.write(self.style.SUCCESS(f'Hid {count} existing marketplace listing(s). Seller data was preserved.'))
