from django.shortcuts import render

# Create your views here.

# backend/users/views.py

from django.contrib.auth.models import User
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .serializers import RegistrationSerializer, UserSerializer


class JWTRegistrationAPIView(generics.CreateAPIView):
    """
    JWT Authentication ile kullanıcı kaydı için API endpoint'i.
    POST isteği ile username, email, password, password2 alır.
    Başarılı kayıtta JWT token'ları (access + refresh) döner.
    """
    queryset = User.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response({
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            },
            "tokens": user.jwt_tokens,
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