from rest_framework import serializers
from .models import Customer, Sale, SaleItem


# Mijoz uchun serializer
class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = "__all__"


# Chekdagi bitta mahsulot qatori uchun serializer (o'qish uchun)
class SaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = SaleItem
        fields = ("id", "product", "product_name", "quantity", "price")


# Chek (sotuv) uchun serializer — o'qish uchun, ichida item'lar bilan birga
class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = Sale
        fields = ("id", "branch", "branch_name", "customer", "customer_name",
                   "total_amount", "payment_type", "created_at", "items")


# Yangi sotuv YARATISH uchun alohida serializer (kiruvchi ma'lumot formati)
class SaleItemCreateSerializer(serializers.Serializer):
    product = serializers.IntegerField()
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2)


class SaleCreateSerializer(serializers.Serializer):
    branch = serializers.IntegerField()
    customer = serializers.IntegerField(required=False, allow_null=True)
    payment_type = serializers.ChoiceField(choices=["naqd", "karta", "qarz"])
    items = SaleItemCreateSerializer(many=True)