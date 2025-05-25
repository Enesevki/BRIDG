from django.shortcuts import render

# Create your views here.

# backend/users/views.py

from django.contrib.auth.models import User
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken # Token almak için hazır view
from rest_framework.authtoken.models import Token # Token modelini import ediyoruz
from .serializers import RegistrationSerializer, UserSerializer


class RegistrationAPIView(generics.CreateAPIView):
    """
    Yeni kullanıcı kaydı için API endpoint'i.
    POST isteği ile username, email, password, password2 alır.
    Başarılı kayıtta kullanıcı bilgilerini (hassas olmayan) döner.
    """
    queryset = User.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.AllowAny] # Herkes kayıt olabilir

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Kayıt sonrası kullanıcıya token döndürmek isteğe bağlıdır.
        # Genellikle kullanıcı kayıt olduktan sonra ayrıca giriş yapar ve token alır.
        # Ancak isterseniz burada token oluşturup döndürebilirsiniz:
        # token, created = Token.objects.get_or_create(user=user)
        # return Response({
        #     "user": UserSerializer(user, context=self.get_serializer_context()).data,
        #     "token": token.key
        # }, status=status.HTTP_201_CREATED)

        # Şimdilik sadece kullanıcı bilgilerini (hassas olmayan) ve başarı mesajı dönelim.
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "message": "Kullanıcı başarıyla oluşturuldu. Lütfen giriş yapın."
        }, status=status.HTTP_201_CREATED)


class LoginAPIView(ObtainAuthToken):
    """
    Kullanıcı girişi için API endpoint'i.
    POST isteği ile username ve password alır.
    Başarılı girişte kullanıcı token'ını ve kullanıcı bilgilerini döner.
    """
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'username': user.username,
            'email': user.email
        })
    

class UserDetailAPIView(generics.RetrieveAPIView):
    """
    Giriş yapmış kullanıcının kendi detaylarını getirmek için API endpoint'i.
    GET isteği ile token gerektirir.
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