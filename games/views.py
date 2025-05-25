from django.shortcuts import render

# Create your views here.

# backend/games/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.db.models import F
from .models import Game, Genre, Tag # Genre ve Tag'i de import etmeyi unutmayın
from .serializers import GameSerializer, GenreSerializer, TagSerializer # Genre ve Tag serializerlarını da
import os # Gerekli olabilir (ama serializer'da kullanıldı)
from django.conf import settings # Gerekli olabilir (ama serializer'da kullanıldı)
# zipfile, default_storage, ContentFile importları artık view'da doğrudan gerekmeyebilir,
# çünkü dosya işleme mantığı serializer'a taşındı. Ancak parse ediciler için kalabilir.
from rest_framework.parsers import MultiPartParser, FormParser # Dosya yüklemeleri için


class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows genres to be viewed.
    Provides `list` and `retrieve` actions.
    """
    queryset = Genre.objects.all().order_by('name')
    serializer_class = GenreSerializer
    permission_classes = [permissions.AllowAny]

    # Varsayılan permission_classes 'AllowAny' (settings.py'den geliyor)
    # Gerekirse burada özelleştirilebilir:
    

class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows tags to be viewed.
    Provides `list` and `retrieve` actions.
    """
    queryset = Tag.objects.all().order_by('name')
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]

    
class GameViewSet(viewsets.ModelViewSet):
    queryset = Game.objects.all().order_by('-created_at') # Şimdilik tüm oyunlar
    serializer_class = GameSerializer
    parser_classes = [MultiPartParser, FormParser] # Dosya yüklemelerini (multipart/form-data) desteklemek için

    def get_queryset(self):
        """
        Sadece yayınlanmış oyunları listeler (eğer kullanıcı admin değilse).
        Admin kullanıcılar tüm oyunları görebilir.
        """
        user = self.request.user
        if user.is_staff or user.is_superuser: # Admin veya staff tümünü görür
            return Game.objects.all().order_by('-created_at')
        return Game.objects.filter(is_published=True).order_by('-created_at')


    def get_permissions(self):
        """
        Aksiyon bazlı izinler.
        """
        if self.action == 'create':
            self.permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Daha sonra özel bir IsOwnerOrReadOnly izni eklenecek.
            # Şimdilik sadece giriş yapmış ve staff olanlar değiştirebilsin/silebilsin.
            self.permission_classes = [permissions.IsAdminUser] # Veya kendi IsOwner izniniz
        else: # list, retrieve
            self.permission_classes = [permissions.AllowAny] # Oyun listesi ve detayı herkese açık
        return super().get_permissions()

    def perform_create(self, serializer):
        """
        Yeni bir Game objesi oluşturulurken creator'ı isteği yapan kullanıcı olarak ayarlar.
        Dosya işleme (zip çıkarma vb.) artık serializer'ın create metodunda yapılıyor.
        """
        serializer.save(creator=self.request.user)
        # Serializer'ın create metodu _process_uploaded_zip'i çağıracak.

    def perform_update(self, serializer):
        """
        Game objesi güncellenirken.
        Dosya işleme (yeni zip varsa) artık serializer'ın update metodunda yapılıyor.
        """
        serializer.save()
        # Serializer'ın update metodu _process_uploaded_zip'i çağıracak (eğer yeni dosya varsa).

    # retrieve metodu view_count artırmak için (önceki gibi)
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        Game.objects.filter(pk=instance.pk).update(view_count=F('view_count') + 1)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    # Eğer özel bir silme mantığı gerekiyorsa perform_destroy override edilebilir.
    # Örneğin, ilişkili dosyaları da sunucudan silmek için.
    # def perform_destroy(self, instance):
    #     # Önce dosyaları sil
    #     if instance.webgl_build_zip and default_storage.exists(instance.webgl_build_zip.name):
    #         default_storage.delete(instance.webgl_build_zip.name)
    #     if instance.thumbnail and default_storage.exists(instance.thumbnail.name):
    #         default_storage.delete(instance.thumbnail.name)
    #     # Çıkarılmış oyun dosyaları klasörünü de silmek gerekebilir (daha karmaşık)
    #     # if instance.entry_point_path:
    #     #     extracted_dir = os.path.dirname(instance.entry_point_path)
    #     #     # Bu klasörü ve içindekileri güvenli bir şekilde silmek için bir fonksiyon
    #     #     # shutil.rmtree(default_storage.path(extracted_dir)) # Dikkatli kullanılmalı!
    #     super().perform_destroy(instance)