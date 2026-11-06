from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        SELLER = "seller", "Seller"
        BUYER = "buyer", "Buyer"
        ADMIN = "admin", "Admin"

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.BUYER)

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)

    @property
    def is_seller(self):
        """Sellers and admins may manage phones."""
        return self.role in (self.Role.SELLER, self.Role.ADMIN)
