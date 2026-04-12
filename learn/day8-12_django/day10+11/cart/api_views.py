from django.db.models import Prefetch
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from orders.serializers import OrderSerializer
from orders.services import create_order_from_cart

from .models import Cart, CartItem
from .serializers import CartItemSerializer, CartSerializer, CheckoutSerializer


class CartViewSet(viewsets.GenericViewSet):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_cart(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user, status=Cart.Status.ACTIVE)
        return (
            Cart.objects.filter(pk=cart.pk)
            .prefetch_related(
                Prefetch(
                    'items',
                    queryset=CartItem.objects.select_related(
                        'product', 'product__category', 'product__supplier'
                    ).prefetch_related('product__images'),
                )
            )
            .first()
        )

    def list(self, request, *args, **kwargs):
        cart = self.get_cart()
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def checkout(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = create_order_from_cart(
            user=request.user,
            shipping_address=serializer.validated_data['shipping_address'],
        )
        order_serializer = OrderSerializer(order)
        return Response(order_serializer.data, status=status.HTTP_201_CREATED)


class CartItemViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(
            cart__user=self.request.user,
            cart__status=Cart.Status.ACTIVE,
        ).select_related('product', 'product__category', 'product__supplier').prefetch_related('product__images')

    def _get_or_create_active_cart(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user, status=Cart.Status.ACTIVE)
        return cart

    def _validate_stock(self, product, quantity):
        if quantity > product.available_stock:
            raise ValueError(f'Insufficient stock for product {product.sku}.')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart = self._get_or_create_active_cart()
        product = serializer.validated_data['product']
        quantity = serializer.validated_data['quantity']

        existing = CartItem.objects.filter(cart=cart, product=product).first()
        new_quantity = quantity if not existing else existing.quantity + quantity

        try:
            self._validate_stock(product, new_quantity)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if existing:
            existing.quantity = new_quantity
            existing.save(update_fields=['quantity', 'updated_at'])
            output = self.get_serializer(existing)
            return Response(output.data, status=status.HTTP_200_OK)

        item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=quantity,
            unit_price_snapshot=product.unit_price,
        )
        output = self.get_serializer(item)
        return Response(output.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        quantity = serializer.validated_data.get('quantity', instance.quantity)
        try:
            self._validate_stock(instance.product, quantity)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        instance.quantity = quantity
        instance.save(update_fields=['quantity', 'updated_at'])
        output = self.get_serializer(instance)
        return Response(output.data)
