from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api_views import CartItemViewSet, CartViewSet

router = DefaultRouter()
router.register(r'items', CartItemViewSet, basename='cart-item')

urlpatterns = [
    path('', CartViewSet.as_view({'get': 'list'}), name='active-cart'),
    path('checkout/', CartViewSet.as_view({'post': 'checkout'}), name='cart-checkout'),
    path('', include(router.urls)),
]
