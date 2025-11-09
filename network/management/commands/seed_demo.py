from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from network.models import Product, Unit


class Command(BaseCommand):
    help = "Создаёт демонстрационные данные: продукты, заводы, розницу и ИП (с долгами и связями)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Очистить связанные таблицы (Units/Products) перед созданием демо-данных.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options.get("reset"):
            self.stdout.write(self.style.WARNING("Удаляю старые данные..."))
            Unit.objects.all().delete()
            Product.objects.all().delete()

        self.stdout.write(self.style.NOTICE("Создаю продукты..."))
        products_data = [
            ("Smart TV", "Q90", "2024-02-15"),
            ("Smartphone", "P12", "2025-06-01"),
            ("Laptop", "L5 Pro", "2023-09-10"),
            ("Tablet", "T10", "2024-11-05"),
            ("Router", "R3000", "2022-05-20"),
        ]
        products = {}
        for name, model, released in products_data:
            p, _ = Product.objects.get_or_create(
                name=name,
                model=model,
                defaults={"released_at": released},
            )
            products[(name, model)] = p

        self.stdout.write(self.style.NOTICE("Создаю заводы (уровень 0)..."))
        factory_a, _ = Unit.objects.get_or_create(
            name="Factory A",
            kind=Unit.Kind.FACTORY,
            email="factory.a@example.com",
            defaults=dict(
                country="DE",
                city="Berlin",
                street="Hauptstr",
                house_number="1",
                supplier=None,
                debt_to_supplier=Decimal("0.00"),
            ),
        )
        factory_b, _ = Unit.objects.get_or_create(
            name="Factory B",
            kind=Unit.Kind.FACTORY,
            email="factory.b@example.com",
            defaults=dict(
                country="PL",
                city="Warsaw",
                street="Koszykowa",
                house_number="10",
                supplier=None,
                debt_to_supplier=Decimal("0.00"),
            ),
        )

        self.stdout.write(
            self.style.NOTICE("Создаю розничные сети (обычно уровень 1)...")
        )
        retail_x, _ = Unit.objects.get_or_create(
            name="Retail X",
            kind=Unit.Kind.RETAIL,
            email="retail.x@example.com",
            defaults=dict(
                country="DE",
                city="Munich",
                street="Marienplatz",
                house_number="7",
                supplier=factory_a,
                debt_to_supplier=Decimal("120000.00"),
            ),
        )
        retail_y, _ = Unit.objects.get_or_create(
            name="Retail Y",
            kind=Unit.Kind.RETAIL,
            email="retail.y@example.com",
            defaults=dict(
                country="PL",
                city="Gdansk",
                street="Dluga",
                house_number="5",
                supplier=factory_b,
                debt_to_supplier=Decimal("80000.00"),
            ),
        )

        self.stdout.write(self.style.NOTICE("Создаю ИП (уровень 1 и 2)..."))
        sp_anna, _ = Unit.objects.get_or_create(
            name="IP Anna",
            kind=Unit.Kind.SP,
            email="ip.anna@example.com",
            defaults=dict(
                country="DE",
                city="Berlin",
                street="Friedrichstr",
                house_number="101",
                supplier=factory_a,  # напрямую от завода → уровень 1
                debt_to_supplier=Decimal("15000.50"),
            ),
        )
        sp_bob, _ = Unit.objects.get_or_create(
            name="IP Bob",
            kind=Unit.Kind.SP,
            email="ip.bob@example.com",
            defaults=dict(
                country="DE",
                city="Munich",
                street="Leopoldstr",
                house_number="23",
                supplier=retail_x,  # через розницу → уровень 2
                debt_to_supplier=Decimal("5200.00"),
            ),
        )
        sp_chen, _ = Unit.objects.get_or_create(
            name="IP Chen",
            kind=Unit.Kind.SP,
            email="ip.chen@example.com",
            defaults=dict(
                country="PL",
                city="Poznan",
                street="Swiety Marcin",
                house_number="12A",
                supplier=retail_y,
                debt_to_supplier=Decimal("0.00"),
            ),
        )

        self.stdout.write(self.style.NOTICE("Привязываю продукты к звеньям..."))
        factory_a.products.set(products.values())
        factory_b.products.set(
            [
                products[("Smartphone", "P12")],
                products[("Laptop", "L5 Pro")],
                products[("Router", "R3000")],
            ]
        )

        retail_x.products.set(
            [
                products[("Smart TV", "Q90")],
                products[("Laptop", "L5 Pro")],
                products[("Router", "R3000")],
            ]
        )
        retail_y.products.set(
            [
                products[("Smartphone", "P12")],
                products[("Tablet", "T10")],
            ]
        )

        sp_anna.products.set(
            [
                products[("Smart TV", "Q90")],
                products[("Router", "R3000")],
            ]
        )
        sp_bob.products.set(
            [
                products[("Laptop", "L5 Pro")],
            ]
        )
        sp_chen.products.set(
            [
                products[("Smartphone", "P12")],
                products[("Tablet", "T10")],
            ]
        )
        self.stdout.write(self.style.SUCCESS("\nГотово! Демо-данные созданы.\n"))
