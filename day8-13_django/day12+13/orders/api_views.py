from django.db.models import Prefetch
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Order, OrderItem
from .serializers import CancelOrderSerializer, OrderSerializer
from .services import cancel_order


class OrderViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        base = (
            Order.objects.select_related("user", "cart")
            .prefetch_related(
                Prefetch(
                    "items",
                    queryset=OrderItem.objects.select_related(
                        "product", "product__category", "product__supplier"
                    ).prefetch_related("product__images"),
                )
            )
            .order_by("-created_at")
        )

        if self.request.user.is_staff:
            return base
        return base.filter(user=self.request.user)

    @action(detail=True, methods=["post"])
    def cancel(self, request, *args, **kwargs):
        order = self.get_object()
        input_serializer = CancelOrderSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        updated_order = cancel_order(
            order=order,
            actor=request.user,
            reason=input_serializer.validated_data.get("reason", ""),
        )
        return Response(self.get_serializer(updated_order).data)
