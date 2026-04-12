import pytest
from rest_framework import status
from rest_framework.exceptions import ValidationError

from cart.models import Cart, CartItem
from inventory.models import StockTransaction
from orders.models import Order
from orders.services import cancel_order, create_order_from_cart


@pytest.mark.django_db
def test_create_order_from_cart_empty_cart_raises_validation_error(normal_user):
    Cart.objects.create(user=normal_user, status=Cart.Status.ACTIVE)

    with pytest.raises(ValidationError):
        create_order_from_cart(user=normal_user, shipping_address="HCM")


@pytest.mark.django_db
def test_create_order_from_cart_insufficient_stock_raises(normal_user, product):
    cart = Cart.objects.create(user=normal_user, status=Cart.Status.ACTIVE)
    CartItem.objects.create(
        cart=cart, product=product, quantity=product.stock_quantity + 1, unit_price_snapshot="1"
    )

    with pytest.raises(ValidationError):
        create_order_from_cart(user=normal_user, shipping_address="HCM")


@pytest.mark.django_db
def test_cancel_order_restocks_inventory(normal_user, product):
    cart = Cart.objects.create(user=normal_user, status=Cart.Status.ACTIVE)
    CartItem.objects.create(
        cart=cart, product=product, quantity=2, unit_price_snapshot=product.unit_price
    )

    order = create_order_from_cart(user=normal_user, shipping_address="District 1")
    product.refresh_from_db()
    stock_after_checkout = product.stock_quantity

    cancel_order(order=order, actor=normal_user, reason="Changed mind")

    order.refresh_from_db()
    product.refresh_from_db()

    assert order.status == Order.Status.CANCELLED
    assert product.stock_quantity == stock_after_checkout + 2
    assert StockTransaction.objects.filter(product=product, transaction_type="IN").exists()


@pytest.mark.django_db
def test_cancel_order_forbidden_for_other_user(normal_user, make_user, product):
    other_user = make_user(username="other_user", email="other@example.com", password="Other@12345")
    cart = Cart.objects.create(user=normal_user, status=Cart.Status.ACTIVE)
    CartItem.objects.create(
        cart=cart, product=product, quantity=1, unit_price_snapshot=product.unit_price
    )
    order = create_order_from_cart(user=normal_user, shipping_address="District 1")

    with pytest.raises(ValidationError):
        cancel_order(order=order, actor=other_user)


@pytest.mark.django_db
def test_orders_list_shows_only_owner_orders(
    api_client, normal_user, make_user, product, auth_headers
):
    other_user = make_user(username="other_user", email="other@example.com", password="Other@12345")

    cart1 = Cart.objects.create(user=normal_user, status=Cart.Status.ACTIVE)
    CartItem.objects.create(
        cart=cart1, product=product, quantity=1, unit_price_snapshot=product.unit_price
    )
    create_order_from_cart(user=normal_user, shipping_address="A")

    product.stock_quantity = 10
    product.save(update_fields=["stock_quantity"])
    cart2 = Cart.objects.create(user=other_user, status=Cart.Status.ACTIVE)
    CartItem.objects.create(
        cart=cart2, product=product, quantity=1, unit_price_snapshot=product.unit_price
    )
    create_order_from_cart(user=other_user, shipping_address="B")

    response = api_client.get("/api/orders/", **auth_headers(normal_user))

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["shipping_address"] == "A"


@pytest.mark.django_db
def test_orders_list_admin_sees_all(api_client, admin_user, normal_user, product, auth_headers):
    cart = Cart.objects.create(user=normal_user, status=Cart.Status.ACTIVE)
    CartItem.objects.create(
        cart=cart, product=product, quantity=1, unit_price_snapshot=product.unit_price
    )
    create_order_from_cart(user=normal_user, shipping_address="A")

    response = api_client.get("/api/orders/", **auth_headers(admin_user))

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) >= 1


@pytest.mark.django_db
def test_cancel_endpoint_rejects_completed_order(api_client, normal_user, product, auth_headers):
    cart = Cart.objects.create(user=normal_user, status=Cart.Status.ACTIVE)
    CartItem.objects.create(
        cart=cart, product=product, quantity=1, unit_price_snapshot=product.unit_price
    )
    order = create_order_from_cart(user=normal_user, shipping_address="A")
    order.status = Order.Status.COMPLETED
    order.save(update_fields=["status"])

    response = api_client.post(
        f"/api/orders/{order.id}/cancel/",
        {"reason": "too late"},
        format="json",
        **auth_headers(normal_user),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
