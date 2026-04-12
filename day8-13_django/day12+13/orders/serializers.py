from rest_framework import serializers

from inventory.serializers import ProductSerializer

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_name_snapshot",
            "product_sku_snapshot",
            "quantity",
            "unit_price",
            "line_total",
            "created_at",
        ]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "customer_email",
            "shipping_address",
            "total_amount",
            "items",
            "created_at",
            "updated_at",
        ]


class CancelOrderSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, max_length=300)
