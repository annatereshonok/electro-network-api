from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Product(models.Model):
    name = models.CharField("Название", max_length=200)
    model = models.CharField("Модель", max_length=200)
    released_at = models.DateField(
        "Дата выхода на рынок", help_text="Дата выхода продукта на рынок"
    )

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"
        unique_together = ("name", "model")
        ordering = ["name", "model"]

    def __str__(self):
        return f"{self.name} {self.model}"


class Unit(models.Model):
    class Kind(models.TextChoices):
        FACTORY = "factory", "Завод"
        RETAIL = "retail", "Розничная сеть"
        SP = "sp", "ИП"

    name = models.CharField("Название звена", max_length=255)
    kind = models.CharField("Тип звена", max_length=20, choices=Kind.choices)

    email = models.EmailField("Email")
    country = models.CharField("Страна", max_length=100)
    city = models.CharField("Город", max_length=100)
    street = models.CharField("Улица", max_length=150)
    house_number = models.CharField("Номер дома", max_length=30)

    supplier = models.ForeignKey(
        "self",
        verbose_name="Поставщик",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="clients",
    )

    products = models.ManyToManyField(
        Product,
        verbose_name="Продукты",
        related_name="units",
        blank=True,
    )

    debt_to_supplier = models.DecimalField(
        "Задолженность перед поставщиком",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        default=Decimal("0.00"),
    )

    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Звено сети"
        verbose_name_plural = "Звенья сети"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def level(self) -> int:
        level = 0
        p = self.supplier
        while p is not None:
            level += 1
            p = p.supplier
        return level

    def clean(self):
        if self.kind == self.Kind.FACTORY and self.supplier is not None:
            raise ValidationError({"supplier": "У завода не может быть поставщика."})

        if self.pk and self.supplier_id == self.pk:
            raise ValidationError(
                {"supplier": "Нельзя указать самого себя как поставщика."}
            )

        cur = self.supplier
        while cur is not None:
            if self.pk and cur.pk == self.pk:
                raise ValidationError(
                    {
                        "supplier": "Цикл в цепочке поставок: поставщик не может быть своим потомком."
                    }
                )
            cur = cur.supplier

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
