import pytest
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from inventory.models import Category, Product, Supplier


@pytest.fixture(autouse=True)
def patch_async_tasks(mocker):
    # Keep tests isolated from Redis/Celery infrastructure.
    mocker.patch("orders.signals.send_order_confirmation_email.delay", return_value=None)
    mocker.patch("inventory.signals.process_product_image.delay", return_value=None)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def make_user(db):
    user_model = get_user_model()

    def _make_user(**kwargs):
        defaults = {
            "username": kwargs.pop("username", "user"),
            "email": kwargs.pop("email", "user@example.com"),
            "password": kwargs.pop("password", "User@12345"),
            "is_staff": kwargs.pop("is_staff", False),
            "is_superuser": kwargs.pop("is_superuser", False),
        }
        return user_model.objects.create_user(**defaults, **kwargs)

    return _make_user


@pytest.fixture
def admin_user(make_user):
    return make_user(
        username="admin_user",
        email="admin_user@example.com",
        password="Admin@12345",
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def normal_user(make_user):
    return make_user(
        username="normal_user",
        email="normal_user@example.com",
        password="User@12345",
    )


@pytest.fixture
def auth_headers():
    def _headers(user):
        token, _ = Token.objects.get_or_create(user=user)
        return {"HTTP_AUTHORIZATION": f"Token {token.key}"}

    return _headers


@pytest.fixture
def category(db):
    return Category.objects.create(name="Electronics")


@pytest.fixture
def supplier(db):
    return Supplier.objects.create(name="Tech Corp", contact_email="supplier@example.com")


@pytest.fixture
def product(category, supplier):
    return Product.objects.create(
        name="Keyboard",
        sku="KB-001",
        category=category,
        supplier=supplier,
        unit_price="100.00",
        stock_quantity=10,
        reorder_level=3,
    )
