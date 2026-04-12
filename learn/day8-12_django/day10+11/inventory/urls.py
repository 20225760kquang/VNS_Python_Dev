from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import CategoryViewSet, SupplierViewSet, ProductViewSet, ProductImageViewSet, StockTransactionViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'suppliers', SupplierViewSet)
router.register(r'products', ProductViewSet, basename='product')
router.register(r'product-images', ProductImageViewSet)
router.register(r'transactions', StockTransactionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
