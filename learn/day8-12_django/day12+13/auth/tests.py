import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token


@pytest.mark.django_db
def test_register_success(api_client):
    payload = {
        "username": "new_user",
        "email": "new_user@example.com",
        "password": "StrongPass@123",
    }
    response = api_client.post("/api/auth/register/", payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert "token" in response.data
    assert response.data["user"]["username"] == payload["username"]
    assert response.data["user"]["role"] == "user"


@pytest.mark.django_db
def test_register_rejects_duplicate_email(api_client, make_user):
    make_user(username="existing", email="dup@example.com")
    payload = {
        "username": "new_user",
        "email": "dup@example.com",
        "password": "StrongPass@123",
    }

    response = api_client.post("/api/auth/register/", payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.data


@pytest.mark.django_db
def test_login_with_email_success(api_client, make_user):
    make_user(username="john", email="john@example.com", password="StrongPass@123")

    response = api_client.post(
        "/api/auth/login/",
        {"identifier": "john@example.com", "password": "StrongPass@123"},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert "token" in response.data
    assert response.data["user"]["username"] == "john"


@pytest.mark.django_db
def test_login_invalid_credentials(api_client, make_user):
    make_user(username="john", email="john@example.com", password="StrongPass@123")

    response = api_client.post(
        "/api/auth/login/",
        {"identifier": "john", "password": "WrongPass@123"},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_me_requires_authentication(api_client):
    response = api_client.get("/api/auth/me/")
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


@pytest.mark.django_db
def test_logout_deletes_token(api_client, normal_user, auth_headers):
    token = Token.objects.create(user=normal_user)
    response = api_client.post("/api/auth/logout/", **auth_headers(normal_user))

    assert response.status_code == status.HTTP_200_OK
    assert not Token.objects.filter(key=token.key).exists()


@pytest.mark.django_db
def test_admin_users_forbidden_for_normal_user(api_client, normal_user, auth_headers):
    response = api_client.get("/api/auth/admin/users/", **auth_headers(normal_user))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_admin_can_update_user_role(api_client, admin_user, normal_user, auth_headers):
    response = api_client.patch(
        f"/api/auth/admin/users/{normal_user.id}/role/",
        {"is_staff": True},
        format="json",
        **auth_headers(admin_user),
    )

    assert response.status_code == status.HTTP_200_OK
    User = get_user_model()
    normal_user.refresh_from_db()
    assert User.objects.get(pk=normal_user.pk).is_staff is True
