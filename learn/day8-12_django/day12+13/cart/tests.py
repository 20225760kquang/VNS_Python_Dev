import pytest
from rest_framework import status

from cart.models import Cart, CartItem
from orders.models import Order


@pytest.mark.django_db
def test_get_cart_creates_active_cart(api_client, normal_user, auth_headers):
    response = api_client.get("/api/cart/", **auth_headers(normal_user))

    assert response.status_code == status.HTTP_200_OK
    assert Cart.objects.filter(user=normal_user, status=Cart.Status.ACTIVE).count() == 1


@pytest.mark.django_db
def test_add_cart_item_success(api_client, normal_user, product, auth_headers):
    response = api_client.post(
        "/api/cart/items/",
        {"product_id": product.id, "quantity": 2},
        format="json",
        **auth_headers(normal_user),
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert CartItem.objects.filter(cart__user=normal_user, product=product, quantity=2).exists()


@pytest.mark.django_db
def test_add_same_product_accumulates_quantity(api_client, normal_user, product, auth_headers):
    api_client.post(
        "/api/cart/items/",
        {"product_id": product.id, "quantity": 2},
        format="json",
        **auth_headers(normal_user),
    )
    response = api_client.post(
        "/api/cart/items/",
        {"product_id": product.id, "quantity": 3},
        format="json",
        **auth_headers(normal_user),
    )

    assert response.status_code == status.HTTP_200_OK
    item = CartItem.objects.get(cart__user=normal_user, product=product)
    assert item.quantity == 5


@pytest.mark.django_db
def test_add_item_insufficient_stock_returns_400(api_client, normal_user, product, auth_headers):
    response = api_client.post(
        "/api/cart/items/",
        {"product_id": product.id, "quantity": product.stock_quantity + 1},
        format="json",
        **auth_headers(normal_user),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_update_item_insufficient_stock_returns_400(api_client, normal_user, product, auth_headers):
    create_response = api_client.post(
        "/api/cart/items/",
        {"product_id": product.id, "quantity": 1},
        format="json",
        **auth_headers(normal_user),
    )
    item_id = create_response.data["id"]

    response = api_client.patch(
        f"/api/cart/items/{item_id}/",
        {"quantity": product.stock_quantity + 5},
        format="json",
        **auth_headers(normal_user),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_checkout_empty_cart_returns_400(api_client, normal_user, auth_headers):
    response = api_client.post(
        "/api/cart/checkout/",
        {"shipping_address": "HCM City"},
        format="json",
        **auth_headers(normal_user),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_checkout_success_creates_order_and_clears_cart(
    api_client, normal_user, product, auth_headers
):
    api_client.post(
        "/api/cart/items/",
        {"product_id": product.id, "quantity": 2},
        format="json",
        **auth_headers(normal_user),
    )

    response = api_client.post(
        "/api/cart/checkout/",
        {"shipping_address": "District 1, HCM"},
        format="json",
        **auth_headers(normal_user),
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert Order.objects.filter(user=normal_user).count() == 1

    active_cart = Cart.objects.get(user=normal_user, status=Cart.Status.CHECKED_OUT)
    assert active_cart.items.count() == 0
