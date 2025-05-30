# backend/users/urls.py

from django.urls import path
from .views import UserDetailAPIView

app_name = 'users_api'  # URL isimleri için namespace (isteğe bağlı ama iyi pratik)

urlpatterns = [
    path('profile/', UserDetailAPIView.as_view(), name='user_profile'),
]