# backend/users/urls.py

from django.urls import path
from .views import RegistrationAPIView, LoginAPIView, UserDetailAPIView
# from .views import LogoutAPIView # Eğer LogoutAPIView'ı eklediyseniz

app_name = 'users_api'  # URL isimleri için namespace (isteğe bağlı ama iyi pratik)

urlpatterns = [
    path('register/', RegistrationAPIView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('profile/', UserDetailAPIView.as_view(), name='user_profile'),
    # path('logout/', LogoutAPIView.as_view(), name='logout'), # Eğer LogoutAPIView'ı eklediyseniz
]