from django.contrib import admin

from .models import Category, Product, ProductImage, StockTransaction, Supplier


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_email", "phone")
    search_fields = ("name", "contact_email")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "sku",
        "name",
        "category",
        "supplier",
        "unit_price",
        "stock_quantity",
        "reorder_level",
        "total_value_display",
        "is_low_stock",
    )
    list_filter = ("category", "supplier")
    search_fields = ("name", "sku")
    list_select_related = ("category", "supplier")
    inlines = [ProductImageInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Apply select_related for N+1 prevention and include the
        # with_total_value annotation from custom QuerySet.
        return qs.select_related("category", "supplier").with_total_value()

    def total_value_display(self, obj):
        # uses the annotated field from with_total_value
        return f"${obj.total_value:,.2f}"

    total_value_display.short_description = "Total Value"
    total_value_display.admin_order_field = "total_value"

    def is_low_stock(self, obj):
        return obj.stock_quantity <= obj.reorder_level

    is_low_stock.boolean = True
    is_low_stock.short_description = "Low Stock"


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ("product", "transaction_type", "quantity", "date")
    list_filter = ("transaction_type", "date")
    search_fields = ("product__name", "notes")
    list_select_related = ("product",)
