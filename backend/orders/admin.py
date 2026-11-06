from django.contrib import admin

from .models import Order, OrderItem, ProblemReport


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("title", "price", "phone", "public_id")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "buyer", "total", "status", "esewa_code", "created_at", "paid_at")
    list_filter = ("status",)
    inlines = [OrderItemInline]


@admin.register(ProblemReport)
class ProblemReportAdmin(admin.ModelAdmin):
    list_display = ("id", "item", "category", "status", "created_at")
    list_filter = ("status", "category")
    list_editable = ("status",)
