from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from sales.views import mijoz_html, hisobot
from products.views import home_view, test_view, ombor_view, filal_view, sozlamalar

from products.api_views import (
    CategoryViewSet, ProductViewSet, BranchViewSet,
    StockViewSet, StockMovementViewSet, branch_summary,
    system_settings_view, change_password_view
)

from sales.api_views import (
    CustomerViewSet, SaleViewSet,
    create_sale, pay_debt, customer_sales_history,
    sales_summary, top_products, daily_sales, low_stock_report
)

router = DefaultRouter()
router.register(r"categories", CategoryViewSet)
router.register(r"products", ProductViewSet)
router.register(r"branches", BranchViewSet)
router.register(r"stock", StockViewSet, basename="stock")
router.register(r"stock-movements", StockMovementViewSet)
router.register(r"customers", CustomerViewSet)
router.register(r"sales", SaleViewSet, basename="sales")

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', home_view, name='home'),
    path('test/', test_view, name='test'),
    path('ombor/', ombor_view, name='ombor_view'),
    path('kassa/', home_view, name='kassa_view'),
    path('mijoz_html/', mijoz_html, name='mijoz_html'),
    path('hisobot/', hisobot, name='hisobot'),
    path('filal_view/', filal_view, name='filal_view'),
    path('sozlamalar/', sozlamalar, name='sozlamalar'),

    path('api/sales/create/', create_sale, name='create_sale'),
    path('api/customers/<int:customer_id>/pay-debt/', pay_debt, name='pay_debt'),
    path('api/customers/<int:customer_id>/history/', customer_sales_history, name='customer_history'),
    path('api/reports/summary/', sales_summary, name='sales_summary'),
    path('api/reports/top-products/', top_products, name='top_products'),
    path('api/reports/daily/', daily_sales, name='daily_sales'),
    path('api/reports/low-stock/', low_stock_report, name='low_stock_report'),
    path('api/branches-summary/', branch_summary, name='branch_summary'),
    path('api/settings/', system_settings_view, name='system_settings'),
    path('api/change-password/', change_password_view, name='change_password'),
    
    path('api/', include(router.urls)),
]