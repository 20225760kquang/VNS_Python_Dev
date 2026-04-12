from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.db.models import Q
from rest_framework import permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    UpdateUserRoleSerializer,
    UserSerializer,
)

User = get_user_model()


class RegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        identifier = serializer.validated_data["identifier"].strip()
        password = serializer.validated_data["password"]

        # Support login by either username or email.
        user_obj = User.objects.filter(
            Q(username__iexact=identifier) | Q(email__iexact=identifier)
        ).first()
        username = user_obj.username if user_obj else identifier

        user = authenticate(request=request, username=username, password=password)
        if not user:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)

        # Also create Django session so DRF browsable API shows logged-in user state.
        django_login(request, user)

        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {"token": token.key, "user": UserSerializer(user).data}, status=status.HTTP_200_OK
        )


class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Remove API token first, then clear Django session.
        token = Token.objects.filter(user=request.user).first()
        if token:
            token.delete()
        django_logout(request)
        return Response({"detail": "Logged out successfully."}, status=status.HTTP_200_OK)


class MeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class AdminUsersAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        users = User.objects.all().order_by("id")
        return Response(UserSerializer(users, many=True).data)


class AdminUserRoleAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, user_id):
        serializer = UpdateUserRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        user.is_staff = serializer.validated_data["is_staff"]
        user.save(update_fields=["is_staff"])
        return Response(UserSerializer(user).data)
