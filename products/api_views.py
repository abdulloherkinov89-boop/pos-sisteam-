from rest_framework import viewsets, filters
from .models import Category, Product, Branch, Stock, StockMovement
from .serializers import (
    CategorySerializer, ProductSerializer, BranchSerializer,
    StockSerializer, StockMovementSerializer
)
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum
from sales.models import Sale
from .models import SystemSettings
from .serializers import SystemSettingsSerializer
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password



# /api/categories/ — kategoriyalarni ko'rish, qo'shish, o'chirish
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


# /api/products/ — faqat faol (is_active=True) mahsulotlarni chiqaradi
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "barcode"]  # ?search=... orqali qidirish mumkin


# /api/branches/ — filiallar ro'yxati
class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer


# /api/stock/ — ombor qoldig'i, ?branch_id=... bilan filial bo'yicha filtrlash mumkin
class StockViewSet(viewsets.ModelViewSet):
    serializer_class = StockSerializer

    def get_queryset(self):
        queryset = Stock.objects.select_related("product", "branch").all()
        branch_id = self.request.query_params.get("branch_id")
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)
        return queryset


# /api/stock-movements/ — ombor harakatlari tarixi, eng yangisi birinchi chiqadi
class StockMovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.select_related("product", "branch").all().order_by("-created_at")
    serializer_class = StockMovementSerializer


@api_view(["GET"])
def branch_summary(request):
    """Har bir filial uchun umumiy ko'rsatkichlar: mahsulot turi, jami qoldiq, jami savdo"""
    branches = Branch.objects.all()
    result = []

    for branch in branches:
        stock_qs = Stock.objects.filter(branch=branch)
        product_count = stock_qs.count()
        total_quantity = stock_qs.aggregate(total=Sum("quantity"))["total"] or 0

        sales_qs = Sale.objects.filter(branch=branch)
        total_sales = sales_qs.aggregate(total=Sum("total_amount"))["total"] or 0
        sales_count = sales_qs.count()

        result.append({
            "id": branch.id,
            "nomi": branch.name,
            "manzil": branch.address,
            "mahsulot_turi": product_count,
            "jami_qoldiq": total_quantity,
            "jami_savdo": total_sales,
            "savdo_soni": sales_count,
        })

    return Response(result)


@api_view(["GET", "PUT"])
def system_settings_view(request):
    settings_obj = SystemSettings.load()

    if request.method == "GET":
        return Response(SystemSettingsSerializer(settings_obj).data)

    serializer = SystemSettingsSerializer(settings_obj, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["POST"])
def change_password_view(request):
    user = request.user
    if not user.is_authenticated:
        return Response({"detail": "Tizimga kirilmagan"}, status=401)

    old_password = request.data.get("old_password")
    new_password = request.data.get("new_password")

    if not old_password or not new_password:
        return Response({"detail": "Eski va yangi parol kiritilishi shart"}, status=400)

    if not check_password(old_password, user.password):
        return Response({"detail": "Eski parol noto'g'ri"}, status=400)

    if len(new_password) < 4:
        return Response({"detail": "Yangi parol kamida 4 belgidan iborat bo'lishi kerak"}, status=400)

    user.set_password(new_password)
    user.save()
    update_session_auth_hash(request, user)

    return Response({"detail": "Parol muvaffaqiyatli o'zgartirildi"})
