from rest_framework import serializers
from .models import Category, Product, Branch, Stock, StockMovement, SystemSettings


# Kategoriya uchun serializer — barcha maydonlarni JSON qilib beradi
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


# Mahsulot uchun serializer
class ProductSerializer(serializers.ModelSerializer):
    # kategoriya nomini alohida ko'rsatish uchun (id o'rniga nom chiqsin)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = "__all__"


# Filial uchun serializer
class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = "__all__"


# Ombor qoldig'i uchun serializer — mahsulot va filial nomini ham qo'shib chiqaradi
class StockSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    barcode = serializers.CharField(source="product.barcode", read_only=True)
    unit = serializers.CharField(source="product.unit", read_only=True)
    sale_price = serializers.DecimalField(source="product.sale_price", max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Stock
        fields = ("id", "product", "product_name", "branch", "branch_name", "barcode", "unit", "sale_price", "quantity")


# Ombor harakatlari tarixi uchun serializer (kirim/chiqim/sotuv)
class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = StockMovement
        fields = "__all__"
        
        
class SystemSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSettings
        fields = ("low_stock_threshold", "currency")
        
        
class SystemSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSettings
        fields = ("low_stock_threshold", "currency")