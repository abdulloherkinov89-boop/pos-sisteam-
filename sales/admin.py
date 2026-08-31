from django.contrib import admin
from .models import Customer, Sale, SaleItem


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "phone", "debt_balance")
    search_fields = ("name", "phone")


# Chek ichidagi mahsulot qatorlarini Sale sahifasining o'zida ko'rsatish uchun
class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("id", "branch", "customer", "total_amount", "payment_type", "created_at")
    list_filter = ("branch", "payment_type")
    search_fields = ("id",)
    inlines = [SaleItemInline]
    readonly_fields = ("created_at",)