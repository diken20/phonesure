from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class PhoneSureUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("PhoneSure", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("PhoneSure", {"fields": ("role",)}),)
    list_display = ("username", "email", "role", "is_active")
    list_filter = ("role", "is_active")
