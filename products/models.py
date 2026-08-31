from django.db import models


class Category(models.Model):
    name = models.CharField("Nomi", max_length=100)

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField("Nomi", max_length=200)
    barcode = models.CharField("Shtrix-kod", max_length=50, unique=True, blank=True, null=True)
    ikpu_code = models.CharField("IKPU kodi", max_length=50, blank=True, null=True)
    unit = models.CharField("O'lchov birligi", max_length=20, default="dona")
    purchase_price = models.DecimalField("Tan narxi", max_digits=12, decimal_places=2, default=0)
    sale_price = models.DecimalField("Sotish narxi", max_digits=12, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Kategoriya")
    is_active = models.BooleanField("Faol", default=True)
    created_at = models.DateTimeField("Yaratilgan sana", auto_now_add=True)

    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"

    def __str__(self):
        return self.name


class Branch(models.Model):
    name = models.CharField("Nomi", max_length=100)
    address = models.CharField("Manzil", max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "Filial"
        verbose_name_plural = "Filiallar"

    def __str__(self):
        return self.name


class Stock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Mahsulot")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, verbose_name="Filial")
    quantity = models.DecimalField("Miqdori", max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Ombor qoldig'i"
        verbose_name_plural = "Ombor qoldiqlari"
        unique_together = ("product", "branch")

    def __str__(self):
        return f"{self.product.name} — {self.branch.name}: {self.quantity}"


class StockMovement(models.Model):
    REASON_CHOICES = [
        ("kirim", "Kirim"),
        ("sotuv", "Sotuv"),
        ("korrektsiya", "Korrektsiya"),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Mahsulot")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, verbose_name="Filial")
    quantity = models.DecimalField("Miqdor (+/-)", max_digits=12, decimal_places=2)
    reason = models.CharField("Sabab", max_length=20, choices=REASON_CHOICES)
    created_at = models.DateTimeField("Sana", auto_now_add=True)

    class Meta:
        verbose_name = "Ombor harakati"
        verbose_name_plural = "Ombor harakatlari"

    def __str__(self):
        return f"{self.product.name}: {self.quantity} ({self.reason})"
    
    
class SystemSettings(models.Model):
    """Tizim bo'yicha umumiy sozlamalar (faqat bitta yozuv bo'ladi)"""
    low_stock_threshold = models.PositiveIntegerField("Kam qoldiq chegarasi", default=10)
    currency = models.CharField("Valyuta belgisi", max_length=10, default="so'm")

    class Meta:
        verbose_name = "Tizim sozlamasi"
        verbose_name_plural = "Tizim sozlamalari"

    def __str__(self):
        return "Tizim sozlamalari"

    def save(self, *args, **kwargs):
        self.pk = 1  # doim faqat bitta yozuv bo'lishini ta'minlaydi
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj