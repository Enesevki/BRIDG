from django.shortcuts import render

# Create your views here.

# backend/users/views.py

from django.contrib.auth.models import User
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from .serializers import RegistrationSerializer, UserSerializer, ChangePasswordSerializer
from gamehost_project.rate_limiting import rate_limit  # Simple rate limiting
import logging

logger = logging.getLogger(__name__)

# İsteğe Bağlı: Logout View
# Token tabanlı sistemde logout genellikle client'ta token'ı silmekle olur.
# Ancak server tarafında token'ı geçersiz kılmak için bir endpoint oluşturulabilir.
# from rest_framework.views import APIView
# class LogoutAPIView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#
#     def post(self, request, *args, **kwargs):
#         try:
#             # Kullanıcının token'ını bul ve sil
#             request.user.auth_token.delete()
#             return Response({"detail": "Başarıyla çıkış yapıldı."}, status=status.HTTP_200_OK)
#         except (AttributeError, Token.DoesNotExist):
#             return Response({"detail": "Token bulunamadı veya zaten çıkış yapılmış."}, status=status.HTTP_400_BAD_REQUEST)

class JWTLogoutAPIView(APIView):
    """
    JWT Logout endpoint that blacklists the refresh token.
    Requires a valid refresh token to be sent in the request.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @rate_limit(requests_per_hour=60, key_type='user')  # 60 logout attempts per hour per user
    def post(self, request, *args, **kwargs):
        try:
            # Get refresh token from request
            refresh_token = request.data.get('refresh_token')
            
            if not refresh_token:
                return Response({
                    "error": True,
                    "message": "Refresh token gereklidir."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create RefreshToken object and blacklist it
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            logger.info(f"User logged out: {request.user.username} (ID: {request.user.id})")
            
            return Response({
                "message": "Başarıyla çıkış yapıldı.",
                "detail": "Token geçersiz kılındı."
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.warning(f"Logout failed for user {request.user.username}: {str(e)}")
            return Response({
                "error": True,
                "message": "Çıkış yapılırken hata oluştu.",
                "detail": "Geçersiz veya süresi dolmuş token."
            }, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordAPIView(APIView):
    """
    Kullanıcı şifre değiştirme endpoint'i.
    Mevcut şifre doğrulaması gerektirir ve güvenli şifre değiştirme sağlar.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @rate_limit(requests_per_hour=10, key_type='user')  # 10 password changes per hour per user
    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Şifre değiştir
            user = serializer.save()
            
            # Yeni JWT token'ları oluştur (güvenlik için)
            refresh = RefreshToken.for_user(user)
            new_tokens = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
            
            logger.info(f"Password changed for user: {user.username} (ID: {user.id})")
            
            return Response({
                "message": "Şifre başarıyla değiştirildi.",
                "detail": "Güvenlik için yeni token'lar oluşturuldu.",
                "tokens": new_tokens
            }, status=status.HTTP_200_OK)
        else:
            logger.warning(f"Password change failed for user {request.user.username}: {serializer.errors}")
            return Response({
                "error": True,
                "message": "Şifre değiştirme başarısız.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

class JWTRegistrationAPIView(generics.CreateAPIView):
    """
    User registration endpoint that returns JWT tokens.
    """
    queryset = User.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]
    
    @rate_limit(requests_per_hour=10, key_type='ip')  # 10 registrations per hour per IP
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        tokens = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        
        return Response({
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            },
            "tokens": tokens,
            "message": "Kullanıcı başarıyla oluşturuldu ve giriş yapıldı."
        }, status=status.HTTP_201_CREATED)
    

class UserDetailAPIView(generics.RetrieveAPIView):
    """
    Giriş yapmış kullanıcının kendi detaylarını getirmek için API endpoint'i.
    GET isteği ile JWT token gerektirir.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated] # Sadece giriş yapmış kullanıcılar erişebilir

    def get_object(self):
        """
        İsteği yapan kullanıcıyı döndürür.
        URL'den bir pk/id almasına gerek kalmaz.
        """
        return self.request.user