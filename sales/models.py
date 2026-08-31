from django.db import models
from products.models import Product, Branch


class Customer(models.Model):
    name = models.CharField("Ismi", max_length=150)
    phone = models.CharField("Telefon", max_length=20, blank=True, null=True)
    debt_balance = models.DecimalField("Qarz balansi", max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Mijoz"
        verbose_name_plural = "Mijozlar"

    def __str__(self):
        return self.name


class Sale(models.Model):
    PAYMENT_CHOICES = [
        ("naqd", "Naqd"),
        ("karta", "Plastik karta"),
        ("qarz", "Nasiya (qarz)"),
    ]

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, verbose_name="Filial")
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Mijoz")
    total_amount = models.DecimalField("Jami summa", max_digits=14, decimal_places=2, default=0)
    payment_type = models.CharField("To'lov turi", max_length=20, choices=PAYMENT_CHOICES, default="naqd")
    created_at = models.DateTimeField("Sana", auto_now_add=True)

    class Meta:
        verbose_name = "Sotuv (chek)"
        verbose_name_plural = "Sotuvlar (cheklar)"

    def __str__(self):
        return f"Chek #{self.id} — {self.total_amount} so'm"


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items", verbose_name="Chek")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Mahsulot")
    quantity = models.DecimalField("Miqdori", max_digits=12, decimal_places=2)
    price = models.DecimalField("Narxi (sotuv paytida)", max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "Chek qatori"
        verbose_name_plural = "Chek qatorlari"

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"