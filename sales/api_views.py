from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from decimal import Decimal, InvalidOperation
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta


from .models import Customer, Sale, SaleItem
from .serializers import CustomerSerializer, SaleSerializer, SaleCreateSerializer
from products.models import Product, Stock


# Mijozlar uchun to'liq CRUD
class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer


# Cheklarni faqat ko'rish uchun (yaratish alohida funksiya orqali bo'ladi)
class SaleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Sale.objects.select_related("branch", "customer").prefetch_related("items").order_by("-created_at")
    serializer_class = SaleSerializer


@api_view(["POST"])
def create_sale(request):
    """
    Yangi sotuv (chek) yaratish.
    - Har bir mahsulot uchun ombordagi qoldiqni tekshiradi
    - Sotuvdan keyin ombordan avtomatik ayiradi
    - Agar to'lov turi "qarz" bo'lsa, mijozning qarz balansini oshiradi
    """
    serializer = SaleCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    branch_id = data["branch"]
    customer_id = data.get("customer")
    payment_type = data["payment_type"]
    items = data["items"]

    if payment_type == "qarz" and not customer_id:
        return Response({"detail": "Qarzga sotish uchun mijoz tanlanishi shart"}, status=400)

    with transaction.atomic():
        total = 0
        checked_items = []

        for item in items:
            try:
                product = Product.objects.get(id=item["product"])
            except Product.DoesNotExist:
                return Response({"detail": f"Mahsulot topilmadi: id={item['product']}"}, status=404)

            try:
                stock = Stock.objects.select_for_update().get(product_id=product.id, branch_id=branch_id)
            except Stock.DoesNotExist:
                return Response({"detail": f"'{product.name}' mahsuloti bu filialda omborga kiritilmagan"}, status=400)

            if stock.quantity < item["quantity"]:
                return Response(
                    {"detail": f"'{product.name}' mahsulotidan omborda yetarli qoldiq yo'q (bor: {stock.quantity})"},
                    status=400
                )

            total += product.sale_price * item["quantity"]
            checked_items.append((product, item["quantity"], stock))

        sale = Sale.objects.create(
            branch_id=branch_id,
            customer_id=customer_id,
            total_amount=total,
            payment_type=payment_type,
        )

        for product, qty, stock in checked_items:
            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=qty,
                price=product.sale_price,
            )
            stock.quantity -= qty
            stock.save()

        if payment_type == "qarz":
            customer = Customer.objects.get(id=customer_id)
            customer.debt_balance += total
            customer.save()

    return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def pay_debt(request, customer_id):
    """Mijozning qarzini (to'liq yoki qisman) to'lash"""
    customer = get_object_or_404(Customer, id=customer_id)
    amount = request.data.get("amount")

    if amount is None:
        return Response({"detail": "Summa kiritilmagan"}, status=400)

    try:
        amount = Decimal(str(amount))
    except (InvalidOperation, ValueError):
        return Response({"detail": "Summa noto'g'ri formatda"}, status=400)

    if amount <= 0:
        return Response({"detail": "Summa musbat bo'lishi kerak"}, status=400)

    if amount > customer.debt_balance:
        return Response({"detail": "To'lov summasi qarzdan katta bo'lishi mumkin emas"}, status=400)

    customer.debt_balance -= amount
    customer.save()

    return Response({"detail": "To'lov qabul qilindi", "qolgan_qarz": str(customer.debt_balance)})


@api_view(["GET"])
def customer_sales_history(request, customer_id):
    """Mijozning barcha xaridlar tarixi"""
    customer = get_object_or_404(Customer, id=customer_id)
    sales = Sale.objects.filter(customer=customer).prefetch_related("items").order_by("-created_at")
    serializer = SaleSerializer(sales, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def sales_summary(request):
    """Umumiy savdo va foyda hisobot (oxirgi N kun uchun, default 30 kun)"""
    days = int(request.query_params.get("days", 30))
    branch_id = request.query_params.get("branch_id")

    since = timezone.now() - timedelta(days=days)
    sales = Sale.objects.filter(created_at__gte=since)
    if branch_id:
        sales = sales.filter(branch_id=branch_id)

    total_revenue = sales.aggregate(total=Sum("total_amount"))["total"] or 0
    total_count = sales.count()

    total_cost = 0
    for sale in sales.prefetch_related("items__product"):
        for item in sale.items.all():
            total_cost += item.product.purchase_price * item.quantity

    return Response({
        "davr_kun": days,
        "jami_savdo_soni": total_count,
        "jami_tushum": total_revenue,
        "jami_tannarx": total_cost,
        "jami_foyda": total_revenue - total_cost,
    })


@api_view(["GET"])
def top_products(request):
    """Eng ko'p sotilgan mahsulotlar"""
    days = int(request.query_params.get("days", 30))
    limit = int(request.query_params.get("limit", 10))
    since = timezone.now() - timedelta(days=days)

    results = (
        SaleItem.objects
        .filter(sale__created_at__gte=since)
        .values("product__name")
        .annotate(
            jami_soni=Sum("quantity"),
            jami_summa=Sum("price")
        )
        .order_by("-jami_soni")[:limit]
    )

    return Response([
        {
            "mahsulot": r["product__name"],
            "jami_soni": r["jami_soni"],
            "jami_summa": r["jami_summa"],
        }
        for r in results
    ])


@api_view(["GET"])
def daily_sales(request):
    """Kunlik savdo dinamikasi (grafik uchun)"""
    days = int(request.query_params.get("days", 14))
    branch_id = request.query_params.get("branch_id")
    since = timezone.now() - timedelta(days=days)

    sales = Sale.objects.filter(created_at__gte=since)
    if branch_id:
        sales = sales.filter(branch_id=branch_id)

    daily = {}
    for sale in sales:
        day = sale.created_at.strftime("%Y-%m-%d")
        daily[day] = daily.get(day, 0) + float(sale.total_amount)

    result = [{"sana": k, "summa": v} for k, v in sorted(daily.items())]
    return Response(result)


@api_view(["GET"])
def low_stock_report(request):
    """Kam qolgan mahsulotlar ro'yxati (chegara: 10 dona)"""
    threshold = int(request.query_params.get("threshold", 10))
    branch_id = request.query_params.get("branch_id")

    items = Stock.objects.filter(quantity__lt=threshold).select_related("product", "branch")
    if branch_id:
        items = items.filter(branch_id=branch_id)

    return Response([
        {
            "mahsulot": item.product.name,
            "filial": item.branch.name,
            "qoldiq": item.quantity,
        }
        for item in items
    ])