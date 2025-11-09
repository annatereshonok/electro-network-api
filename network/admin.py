from decimal import Decimal

from django.contrib import admin
from django.utils.html import format_html

from .models import Product, Unit


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "model", "released_at")
    search_fields = ("name", "model")
    list_filter = ("released_at",)


@admin.action(description="Очистить задолженность у выбранных звеньев")
def clear_debt(modeladmin, request, queryset):
    updated = queryset.update(debt_to_supplier=Decimal("0.00"))
    modeladmin.message_user(request, f"Обнулено: {updated}")


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "kind",
        "city",
        "country",
        "supplier_link",
        "debt_to_supplier",
        "level",
        "created_at",
    )
    list_filter = ("city", "kind", "country")
    search_fields = ("name", "city", "country", "email")
    filter_horizontal = ("products",)
    actions = [clear_debt]

    @admin.display(description="Поставщик", ordering="supplier__name")
    def supplier_link(self, obj: Unit):
        if not obj.supplier:
            return "—"
        url = f"/admin/network/unit/{obj.supplier_id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.supplier.name)
