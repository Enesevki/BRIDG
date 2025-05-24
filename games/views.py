from django.shortcuts import render

# Create your views here.

# backend/games/views.py

from rest_framework import viewsets, permissions
from .models import Genre, Tag, Game
from .serializers import GenreSerializer, TagSerializer, GameSerializer


class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows genres to be viewed.
    Provides `list` and `retrieve` actions.
    """
    queryset = Genre.objects.all().order_by('name') # Tüm Genre objelerini isme göre sıralı getir
    serializer_class = GenreSerializer
    # Varsayılan permission_classes 'AllowAny' (settings.py'den geliyor)
    # Gerekirse burada özelleştirilebilir:
    # permission_classes = [permissions.AllowAny]


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows tags to be viewed.
    Provides `list` and `retrieve` actions.
    """
    queryset = Tag.objects.all().order_by('name') # Tüm Tag objelerini isme göre sıralı getir
    serializer_class = TagSerializer
    # permission_classes = [permissions.AllowAny]
    

class GameViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows games to be viewed.
    Provides `list` and `retrieve` actions.
    Sadece yayınlanmış (is_published=True) oyunları listeler.
    """
    # Sadece yayınlanmış ve en yeni oyunları önce gösterecek şekilde ayarlandı.
    queryset = Game.objects.filter(is_published=True).order_by('-created_at')
    serializer_class = GameSerializer
    # permission_classes = [permissions.AllowAny]

    # Eğer belirli bir oyunun detayını getirirken view_count'u artırmak istersek:
    # (Bu daha sonraki bir adımda daha detaylı ele alınabilir)
    # def retrieve(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     # instance.view_count += 1 # Basit artırma (atomik değil)
    #     # instance.save(update_fields=['view_count']) # Sadece view_count'u güncelle
    #     # Atomik artırma için F objesi kullanılabilir:
    #     # from django.db.models import F
    #     # Game.objects.filter(pk=instance.pk).update(view_count=F('view_count') + 1)
    #     # instance.refresh_from_db(fields=['view_count'])
    #     serializer = self.get_serializer(instance)
    #     return Response(serializer.data)