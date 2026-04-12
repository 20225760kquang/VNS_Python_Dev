from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework import serializers

from inventory.models import Product
from inventory.serializers import ProductSerializer

from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product", write_only=True
    )
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product",
            "product_id",
            "quantity",
            "unit_price_snapshot",
            "subtotal",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "unit_price_snapshot", "created_at", "updated_at"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "status", "items", "total_amount", "created_at", "updated_at"]

    def get_total_amount(self, obj):
        subtotal_expr = ExpressionWrapper(
            F("quantity") * F("unit_price_snapshot"),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
        return obj.items.aggregate(
            total=Coalesce(
                Sum(subtotal_expr),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )["total"]


class CheckoutSerializer(serializers.Serializer):
    shipping_address = serializers.CharField(max_length=500)
