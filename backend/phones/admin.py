from django.contrib import admin

from .models import Phone, PhoneModelReference


@admin.register(PhoneModelReference)
class PhoneModelReferenceAdmin(admin.ModelAdmin):
    list_display = ("brand", "model_name", "storage_gb", "base_price")
    list_filter = ("brand",)
    search_fields = ("brand", "model_name")


@admin.register(Phone)
class PhoneAdmin(admin.ModelAdmin):
    list_display = ("reference", "owner", "condition", "asking_price", "status", "created_at")
    list_filter = ("status", "condition")
    readonly_fields = ("reviewed_at",)
