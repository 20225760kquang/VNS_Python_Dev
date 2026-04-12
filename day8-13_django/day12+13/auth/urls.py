from django.urls import path

from .views import (
    AdminUserRoleAPIView,
    AdminUsersAPIView,
    LoginAPIView,
    LogoutAPIView,
    MeAPIView,
    RegisterAPIView,
)

urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="auth-register"),
    path("login/", LoginAPIView.as_view(), name="auth-login"),
    path("logout/", LogoutAPIView.as_view(), name="auth-logout"),
    path("me/", MeAPIView.as_view(), name="auth-me"),
    path("admin/users/", AdminUsersAPIView.as_view(), name="auth-admin-users"),
    path(
        "admin/users/<int:user_id>/role/",
        AdminUserRoleAPIView.as_view(),
        name="auth-admin-user-role",
    ),
]
