from typing import Optional

from django.db.models.functions import Lower
from rest_framework import serializers

from network.models import Product, Unit


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("id", "name", "model", "released_at")


class UnitSerializer(serializers.ModelSerializer):
    level = serializers.IntegerField(read_only=True)
    debt_to_supplier = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    created_at = serializers.DateTimeField(read_only=True)
    products = ProductSerializer(read_only=True, many=True)
    product_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        required=False,
        source="products",
        queryset=Product.objects.all(),
    )

    class Meta:
        model = Unit
        fields = (
            "id",
            "name",
            "kind",
            "email",
            "country",
            "city",
            "street",
            "house_number",
            "supplier",
            "products",
            "product_ids",
            "debt_to_supplier",
            "level",
            "created_at",
        )
        read_only_fields = ("products", "debt_to_supplier", "level", "created_at")

    def validate_email(self, value: str) -> str:
        v = (value or "").strip().lower()
        qs = Unit.objects.annotate(email_l=Lower("email")).filter(email_l=v)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "Такой email уже используется другим звеном."
            )
        return v

    def validate_supplier(self, supplier: Optional[Unit]) -> Optional[Unit]:
        inst = getattr(self, "instance", None)
        if not inst or supplier is None:
            return supplier

        if supplier.pk == inst.pk:
            raise serializers.ValidationError(
                "Нельзя указать самого себя как поставщика."
            )

        cur = supplier
        while cur is not None:
            if cur.pk == inst.pk:
                raise serializers.ValidationError(
                    "Цепочка поставок станет циклической."
                )
            cur = cur.supplier
        return supplier

    def validate(self, attrs):
        email = attrs.get("email")
        if email is not None:
            attrs["email"] = email.strip().lower()
        return attrs

    def create(self, validated_data):
        products = validated_data.pop("products", [])
        unit = super().create(validated_data)
        if products:
            unit.products.set(products)
        return unit

    def update(self, instance, validated_data):
        products = validated_data.pop("products", None)
        unit = super().update(instance, validated_data)
        if products is not None:
            unit.products.set(products)
        return unit
