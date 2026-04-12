from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Category, Product, ProductImage, StockTransaction, Supplier
from .serializers import (
    CategorySerializer,
    ProductImageSerializer,
    ProductSerializer,
    StockTransactionSerializer,
    SupplierSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Categories to be viewed or edited.
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAdminUser]


class SupplierViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Suppliers to be viewed or edited.
    """

    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAdminUser]


class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Products to be viewed or edited.
    Provides custom actions for advanced ORM concepts.
    """

    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        # Always use select_related and the annotated with_total_value by default
        return (
            Product.objects.with_total_value()
            .select_related("category", "supplier")
            .prefetch_related("images")
            .order_by("id")
        )

    @action(detail=False, methods=["get"])
    def low_stock(self, request):
        """
        Returns a list of products that have stock less than or equal to their reorder level.
        """
        # Re-using the custom QuerySet low_stock() method
        queryset = self.get_queryset().low_stock()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """
        Returns total inventory value and overall counts.
        """
        total_value = Product.objects.total_inventory_value()
        return Response(
            {
                "total_inventory_value": total_value,
                "total_products": Product.objects.count(),
                "total_categories": Category.objects.count(),
                "total_suppliers": Supplier.objects.count(),
            }
        )


class StockTransactionViewSet(viewsets.ModelViewSet):
    """
    API endpoint to log and view Stock Transactions.
    """

    queryset = StockTransaction.objects.select_related("product").all().order_by("-date")
    serializer_class = StockTransactionSerializer
    permission_classes = [permissions.IsAdminUser]


class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.select_related("product").all().order_by("-created_at")
    serializer_class = ProductImageSerializer
    permission_classes = [permissions.IsAdminUser]
