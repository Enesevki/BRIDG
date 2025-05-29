# backend/games/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views # games/views.py dosyasını import ediyoruz

# DefaultRouter, ViewSet'ler için otomatik olarak URL pattern'leri oluşturur.
# Örneğin, /genres/ listeleme ve yeni oluşturma için, /genres/{pk}/ detay, güncelleme, silme için.
router = DefaultRouter()
router.register(r'genres', views.GenreViewSet, basename='genre') # 'genre' URL ön eki, GenreViewSet'i kullanacak
router.register(r'tags', views.TagViewSet, basename='tag')     # 'tag' URL ön eki, TagViewSet'i kullanacak
router.register(r'games', views.GameViewSet, basename='game')   # 'game' URL ön eki, GameViewSet'i kullanacak

# API URL'lerimiz router tarafından otomatik olarak yönetiliyor.
urlpatterns = [
    path('', include(router.urls)),  # Router tarafından oluşturulan URL'leri dahil et
    path('analytics/my-games/', views.MyGamesAnalyticsListView.as_view(), name='my_games_analytics'),
]
