from rest_framework                           import generics, status
from rest_framework.views                     import APIView
from rest_framework.response                  import Response
from rest_framework.permissions               import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens          import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from .models       import User
from .serializers  import (
    RegisterSerializer,
    UserSerializer,
    ProfileUpdateSerializer,
    ChangePasswordSerializer,
)

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# ─── Register ──────────────────────────────────────────────────────────#

class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/"""
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Issue tokens immediately after registration
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Account created successfully.',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access':  str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


# ─── Login ────────────────────────────────────────────────────────────────────

class LoginView(APIView):
    """POST /api/auth/login/"""
    permission_classes = [AllowAny]

    @method_decorator(csrf_exempt, name='dispatch')
    def post(self, request):
        from django.contrib.auth import authenticate
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')

        if not username or not password:
            return Response(
                {'error': 'Username and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Allow login by email OR username
        user = None
        if '@' in username:
            try:
                u = User.objects.get(email__iexact=username)
                user = authenticate(request, username=u.username, password=password)
            except User.DoesNotExist:
                pass
        else:
            user = authenticate(request, username=username, password=password)

        if user is None:
            return Response(
                {'error': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access':  str(refresh.access_token),
            }
        })


# ─── Logout ───────────────────────────────────────────────────────────────────

class LogoutView(APIView):
    """POST /api/auth/logout/  — blacklists the refresh token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response(
                {'error': 'Invalid or already-blacklisted token.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response({'message': 'Logged out successfully.'})


# ─── Profile ──────────────────────────────────────────────────────────────────

class ProfileView(APIView):
    """GET/PUT/PATCH /api/auth/profile/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(request.user, serializer.validated_data)
        return Response(UserSerializer(request.user).data)

    def put(self, request):
        return self.patch(request)


# ─── Change Password ──────────────────────────────────────────────────#

class ChangePasswordView(APIView):
    """POST /api/auth/change-password/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Password changed successfully.'})


# ─── Delete Account ───────────────────────────────────────────────────────#

class DeleteAccountView(APIView):
    """DELETE /api/auth/delete-account/"""
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        password = request.data.get('password')
        if not password:
            return Response(
                {'error': 'Password confirmation is required to delete your account.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not request.user.check_password(password):
            return Response(
                {'error': 'Incorrect password.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        request.user.delete()
        return Response(
            {'message': 'Account deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT
        )
