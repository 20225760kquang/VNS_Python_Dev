import pytest
from rest_framework import status

from inventory.models import Product


@pytest.mark.django_db
def test_inventory_requires_admin_for_read(api_client, normal_user, auth_headers):
    response = api_client.get("/api/inventory/categories/", **auth_headers(normal_user))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_inventory_admin_can_create_category(api_client, admin_user, auth_headers):
    response = api_client.post(
        "/api/inventory/categories/",
        {"name": "Office"},
        format="json",
        **auth_headers(admin_user),
    )
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_inventory_admin_summary_contains_expected_keys(api_client, admin_user, auth_headers):
    response = api_client.get("/api/inventory/products/summary/", **auth_headers(admin_user))

    assert response.status_code == status.HTTP_200_OK
    assert "total_inventory_value" in response.data
    assert "total_products" in response.data
    assert "total_categories" in response.data
    assert "total_suppliers" in response.data


@pytest.mark.django_db
def test_low_stock_endpoint_returns_only_low_stock_products(
    api_client,
    admin_user,
    auth_headers,
    category,
    supplier,
):
    low = Product.objects.create(
        name="Low Product",
        sku="LOW-001",
        category=category,
        supplier=supplier,
        unit_price="10.00",
        stock_quantity=2,
        reorder_level=3,
    )
    Product.objects.create(
        name="Normal Product",
        sku="NOR-001",
        category=category,
        supplier=supplier,
        unit_price="12.00",
        stock_quantity=20,
        reorder_level=3,
    )

    response = api_client.get("/api/inventory/products/low_stock/", **auth_headers(admin_user))

    assert response.status_code == status.HTTP_200_OK
    returned_skus = {item["sku"] for item in response.data}
    assert low.sku in returned_skus
    assert "NOR-001" not in returned_skus


@pytest.mark.django_db
def test_product_queryset_total_inventory_value_returns_number(product):
    total = Product.objects.total_inventory_value()
    assert total is not None
    assert float(total) > 0
