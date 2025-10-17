from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserRegistrationSerializer,
    UserSerializer,
    ChangePasswordSerializer,
    UserUpdateSerializer
)
from .models import User


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT Login View
    POST /api/auth/login/
    Body: {"username": "admin", "password": "123456"}
    Response: {"access": "token...", "refresh": "token...", "user": {...}}
    """
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    """
    User Registration View
    POST /api/auth/register/
    Body: {
        "username": "newuser",
        "email": "user@example.com",
        "password": "password123",
        "password2": "password123",
        "first_name": "John",
        "last_name": "Doe"
    }
    """
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens for the newly created user
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'User registered successfully!'
        }, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    """
    Logout View - Blacklist refresh token
    POST /api/auth/logout/
    Body: {"refresh": "refresh_token..."}
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            token = RefreshToken(refresh_token)
            token.blacklist()  # Blacklist token

            return Response({
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    User Profile View
    GET /api/auth/profile/ - Xem profile
    PUT/PATCH /api/auth/profile/ - Update profile
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserDetailView(generics.RetrieveAPIView):
    """
    Public User Detail View
    GET /api/users/<id>/ - Xem profile user khác
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


class UpdateProfileView(generics.UpdateAPIView):
    """
    Update User Profile
    PUT/PATCH /api/auth/profile/update/
    """
    serializer_class = UserUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """
    Change Password View
    POST /api/auth/change-password/
    Body: {
        "old_password": "old123",
        "new_password": "new123",
        "new_password2": "new123"
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            # Set new password
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()

            return Response({
                'message': 'Password changed successfully'
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListView(generics.ListAPIView):
    """
    List all users (Admin only)
    GET /api/users/
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


class DeleteAccountView(APIView):
    """
    Delete User Account
    DELETE /api/auth/delete-account/
    Body: {"password": "user_password"}
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        password = request.data.get('password')

        if not password:
            return Response(
                {'error': 'Password is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user

        # Verify password
        if not user.check_password(password):
            return Response(
                {'error': 'Incorrect password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Delete user
        username = user.username
        user.delete()

        return Response({
            'message': f'Account {username} deleted successfully'
        }, status=status.HTTP_200_OK)
