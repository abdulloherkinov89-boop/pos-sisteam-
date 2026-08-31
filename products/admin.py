from django.contrib import admin
from .models import Category, Product, Branch, Stock, StockMovement
from .models import SystemSettings



@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "barcode", "unit", "purchase_price", "sale_price", "category", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("name", "barcode", "ikpu_code")
    list_editable = ("sale_price", "is_active")


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "address")
    search_fields = ("name",)


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "branch", "quantity")
    list_filter = ("branch",)
    search_fields = ("product__name",)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "branch", "quantity", "reason", "created_at")
    list_filter = ("branch", "reason")
    search_fields = ("product__name",)
    readonly_fields = ("created_at",)
    

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ("low_stock_threshold", "currency")