import random
from decimal import Decimal

from django.core.management.base import BaseCommand

from products.models import Branch, Category, Product, Stock, StockMovement


class Command(BaseCommand):
    help = "Demo filiallar, kategoriyalar, mahsulotlar va ombor qoldiqlarini yaratadi."

    def add_arguments(self, parser):
        parser.add_argument("--branches", type=int, default=8)
        parser.add_argument("--products", type=int, default=150)
        parser.add_argument("--seed", type=int, default=20260911)

    def handle(self, *args, **options):
        generator = random.Random(options["seed"])
        branch_count = options["branches"]
        product_count = options["products"]

        category_names = [
            "Ichimliklar", "Oziq-ovqat", "Sut mahsulotlari", "Shirinliklar",
            "Gigiyena", "Maishiy kimyo", "Kanselyariya", "Elektronika",
            "Go'sht mahsulotlari", "Meva-sabzavotlar", "Non mahsulotlari",
            "Chaqaloqlar uchun", "Uy-ro'zg'or", "Kiyim-kechak", "Avto mahsulotlar",
        ]
        categories = [
            Category.objects.get_or_create(name=name)[0]
            for name in category_names
        ]

        branches = []
        for index in range(1, branch_count + 1):
            branch, _ = Branch.objects.get_or_create(
                name=f"{index}-filial",
                defaults={"address": f"Toshkent shahri, {index}-mavze, {index}-uy"},
            )
            branches.append(branch)

        product_prefixes = [
            "Premium", "Baraka", "Oltin", "Sifat", "Zarafshon", "Navruz",
            "Mehr", "Lazzat", "Toshkent", "Samarqand", "Fayz", "Orzu",
        ]
        product_names = [
            "Choy", "Qahva", "Shakar", "Guruch", "Makaron", "Yog'", "Un",
            "Sut", "Qatiq", "Pishloq", "Kolbasa", "Non", "Suv", "Sharbat",
            "Pechenye", "Shokolad", "Sovun", "Shampun", "Tish pastasi", "Batareya",
        ]

        products = []
        for index in range(1, product_count + 1):
            barcode = f"200{index:010d}"
            product, created = Product.objects.get_or_create(
                barcode=barcode,
                defaults={
                    "name": f"{generator.choice(product_prefixes)} {generator.choice(product_names)} {index}",
                    "ikpu_code": f"{generator.randint(100000, 999999)}",
                    "unit": generator.choice(["dona", "kg", "litr", "quti"]),
                    "purchase_price": Decimal(generator.randint(500, 250000)),
                    "sale_price": Decimal(generator.randint(1000, 350000)),
                    "category": generator.choice(categories),
                    "is_active": True,
                },
            )
            products.append(product)

        stock_count = 0
        movement_count = 0
        for branch in branches:
            for product in products:
                quantity = Decimal(generator.randint(0, 500))
                stock, created = Stock.objects.get_or_create(
                    branch=branch,
                    product=product,
                    defaults={"quantity": quantity},
                )
                if not created:
                    stock.quantity = quantity
                    stock.save(update_fields=["quantity"])
                stock_count += 1

                if created:
                    StockMovement.objects.create(
                        branch=branch,
                        product=product,
                        quantity=quantity,
                        reason="kirim",
                    )
                    movement_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Tayyor: {len(branches)} filial, {len(products)} mahsulot, "
            f"{stock_count} qoldiq, {movement_count} kirim harakati, "
            f"{len(categories)} kategoriya."
        ))
        self.stdout.write("Shtrix-kodlar: 2000000000001 dan boshlab unique 13 xonali kodlar.")
