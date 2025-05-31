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
from .serializers import (
    RegistrationSerializer, UserSerializer, ChangePasswordSerializer,
    EmailVerificationSerializer, ResendVerificationSerializer, 
    EmailVerificationStatusSerializer
)
from .email_service import EmailVerificationService
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
    User registration endpoint with email verification.
    Sends verification email after successful registration.
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
        
        # Email verification kodu oluştur ve gönder
        verification_code = user.profile.generate_verification_code()
        email_sent = EmailVerificationService.send_verification_email(user, verification_code)
        
        response_data = {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            },
            "tokens": tokens,
            "email_verified": False,  # Henüz doğrulanmadı
            "message": "Kullanıcı başarıyla oluşturuldu ve giriş yapıldı."
        }
        
        if email_sent:
            response_data["email_verification"] = {
                "sent": True,
                "message": "Doğrulama kodu email adresinize gönderildi.",
                "expires_in_minutes": 15
            }
            logger.info(f"User registered with email verification: {user.username} (ID: {user.id})")
        else:
            response_data["email_verification"] = {
                "sent": False,
                "message": "Email gönderilemedi, lütfen daha sonra tekrar deneyin.",
                "warning": "Email servisi aktif değil - console'u kontrol edin."
            }
            logger.warning(f"User registered but email failed: {user.username} (ID: {user.id})")
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    

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


# =============================================================================
# EMAIL VERIFICATION VIEWS
# =============================================================================

class EmailVerificationAPIView(APIView):
    """
    Email doğrulama kodu ile email adresini doğrular.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @rate_limit(requests_per_hour=30, key_type='user')  # 30 verification attempts per hour
    def post(self, request, *args, **kwargs):
        serializer = EmailVerificationSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Email doğrulamasını gerçekleştir
            user = serializer.save()
            
            # Hoş geldin email'i gönder (opsiyonel)
            EmailVerificationService.send_welcome_email(user)
            
            return Response({
                "message": "Email başarıyla doğrulandı!",
                "email_verified": True,
                "user": {
                    "username": user.username,
                    "email": user.email
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "error": True,
                "message": "Email doğrulama başarısız.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationAPIView(APIView):
    """
    Doğrulama kodunu yeniden gönderir.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @rate_limit(requests_per_hour=5, key_type='user')  # 5 resend attempts per hour
    def post(self, request, *args, **kwargs):
        serializer = ResendVerificationSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = request.user
            
            # Yeni doğrulama kodu oluştur
            verification_code = user.profile.generate_verification_code()
            
            # Email gönder
            email_sent = EmailVerificationService.send_verification_email(user, verification_code)
            
            if email_sent:
                return Response({
                    "message": "Doğrulama kodu tekrar gönderildi.",
                    "expires_in_minutes": 15,
                    "attempts_remaining": max(0, 5 - user.profile.verification_attempts)
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "error": True,
                    "message": "Email gönderilemedi.",
                    "detail": "Email servisi şu anda kullanılamıyor."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                "error": True,
                "message": "Kod yeniden gönderilemedi.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)


class EmailVerificationStatusAPIView(APIView):
    """
    Email doğrulama durumunu gösterir.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = EmailVerificationStatusSerializer(user)
        
        return Response({
            "user": {
                "username": user.username,
                "email": user.email
            },
            "verification_status": serializer.data
        }, status=status.HTTP_200_OK)