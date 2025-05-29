from django.shortcuts import render

# Create your views here.

# backend/games/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser  # Dosya yüklemeleri için
from django.db.models import F, Q, Count  # Count ve Q'yu import etmeyi unutmayın
from .models import Game, Genre, Tag  # Model importları
from .serializers import (  # Serializer importları
    GameSerializer, GenreSerializer, TagSerializer, GameUpdateSerializer
)
from django.core.files.storage import default_storage
import os
import shutil
from .permissions import IsOwnerOrReadOnly  # Yeni izin sınıfımız

# interactions uygulamasının modellerini ve serializer'larını import et
from interactions.models import Rating, Report
from interactions.serializers import RatingSerializer, ReportSerializer


class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Genre.objects.all().order_by('name')
    serializer_class = GenreSerializer
    permission_classes = [permissions.AllowAny]


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all().order_by('name')
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]


class GameViewSet(viewsets.ModelViewSet):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    lookup_field = 'id'  # Primary key alanımızın adı 'id' olduğu için

    # Ana queryset'i burada tanımlıyoruz. get_queryset() bunu daha da filtreleyecek.
    # Sinyallerle likes_count ve dislikes_count'u güncellediğimiz için,
    # burada annotate etmeye genellikle gerek yok. Modeldeki alanlar kullanılacak.
    # Eğer anlık sayım istenseydi veya sinyal olmasaydı annotate gerekirdi.
    # Şimdilik sinyallere güvendiğimiz için annotate'i kaldırıyoruz.
    queryset = Game.objects.all().order_by('-created_at')

    def get_queryset(self):
        """
        Kullanıcının rolüne ve oyunun yayın durumuna göre oyunları döndürür.
        Bu queryset hem listeleme hem de detay getirme için temel oluşturur.
        """
        user = self.request.user
        # Temel queryset'i alalım (yukarıdaki sınıf seviyesindeki queryset)
        base_queryset = super().get_queryset()

        if user.is_authenticated:
            if user.is_staff or user.is_superuser:
                # Admin/Staff tüm oyunları görür
                return base_queryset
            else:
                # Giriş yapmış normal kullanıcılar, kendi yayınlanmamış oyunlarını
                # VE tüm yayınlanmış oyunları görür.
                return base_queryset.filter(
                    Q(is_published=True) | Q(creator=user)
                ).distinct()  # distinct() önemli
        else:
            # Anonim kullanıcılar sadece yayınlanmış oyunları görür
            return base_queryset.filter(is_published=True)

    def get_serializer_class(self):
        """
        Aksiyona göre uygun serializer sınıfını döndürür.
        """
        if self.action in ['update', 'partial_update']:
            return GameUpdateSerializer  # Güncelleme işlemleri için bu serializer kullanılacak
        return GameSerializer  # Diğer tüm aksiyonlar için (create, list, retrieve)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()  # İzin kontrolü (IsOwnerOrReadOnly) burada yapılır

        # Gelen veriyi GameUpdateSerializer ile doğrula
        # partial=True (PATCH için) veya partial=False (PUT için)
        update_serializer = self.get_serializer(instance, data=request.data, partial=partial)
        update_serializer.is_valid(raise_exception=True)
        
        # perform_update'ı çağır (ModelViewSet'teki varsayılan veya bizim override ettiğimiz)
        self.perform_update(update_serializer)  # Bu serializer.save() çağırır

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been used, then relation needs to be
            # reloaded from the database.
            instance._prefetched_objects_cache = {}

        # Güncellenmiş instance'ı ana GameSerializer ile yanıt olarak döndür
        response_serializer = GameSerializer(instance, context={'request': request})
        return Response(response_serializer.data)

    # partial_update metodu ModelViewSet'te update'i partial=True ile çağırır,
    # bu yüzden yukarıdaki update metodu PATCH için de çalışır.
    # Ayrı bir partial_update yazmaya genellikle gerek kalmaz.

    def get_permissions(self):
        """
        Aksiyon bazlı izinler.
        """
        if self.action == 'create':
            self.permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy', 'retrieve']:
            # retrieve için IsOwnerOrReadOnly, objenin yayın durumunu ve sahipliğini kontrol eder.
            # update, partial_update, destroy için ise sadece sahiplik kontrolü yapar (IsOwnerOrReadOnly'nin mevcut tanımına göre).
            self.permission_classes = [IsOwnerOrReadOnly]
        elif self.action in ['rate_game', 'unrate_game', 'report_game']:
            self.permission_classes = [permissions.IsAuthenticated]
        else:  # list
            self.permission_classes = [permissions.AllowAny]
        return super().get_permissions()

    def perform_create(self, serializer):
        """
        Yeni bir Game objesi oluşturulurken creator'ı isteği yapan kullanıcı olarak ayarlar.
        Dosya işleme (zip çıkarma vb.) serializer'ın create metodunda yapılıyor.
        """
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        """
        Game objesi güncellenirken.
        Dosya işleme (yeni zip varsa) serializer'ın update metodunda yapılıyor.
        """
        # GameUpdateSerializer'da zip dosyası güncellenmeyeceği için
        # serializer.save() yeterli olacaktır.
        serializer.save()

    def perform_destroy(self, instance):
        # ... (önceki cevaptaki dosya silme mantığı) ...
        # ÖNEMLİ: default_storage, os, shutil importları gerekli

        original_zip_path = instance.webgl_build_zip.name if instance.webgl_build_zip else None
        original_thumbnail_path = instance.thumbnail.name if instance.thumbnail else None
        entry_point_full_path = instance.entry_point_path # Bu zaten MEDIA_ROOT'a göreceli olmalı

        # Önce veritabanından objeyi sil (sinyaller varsa önce çalışır)
        instance_id_str = str(instance.id)  # ID'yi silmeden önce al
        instance.delete() 
        print(f"Oyun {instance_id_str} veritabanından silindi.")

        # Sonra dosyaları sil
        if original_zip_path and default_storage.exists(original_zip_path):
            default_storage.delete(original_zip_path)
            print(f"Zip dosyası silindi: {original_zip_path}")
        if original_thumbnail_path and default_storage.exists(original_thumbnail_path):
            default_storage.delete(original_thumbnail_path)
            print(f"Thumbnail silindi: {original_thumbnail_path}")
        
        if entry_point_full_path:  # entry_point_path, çıkarılmış klasördeki index.html'in yoluydu
            try:
                # Çıkarılmış oyun dosyalarının bulunduğu ana klasörü bulmaya çalış
                # entry_point_path: game_builds/extracted/<uuid>/[kök_klasör/]index.html
                # extraction_game_dir_segment: game_builds/extracted/<uuid>
                extraction_game_dir_segment = os.path.join('game_builds', 'extracted', instance_id_str)
                # default_storage.path() yerel dosya sistemi için çalışır.
                # Bulut depolama için bu kısım farklılık gösterebilir.
                try:
                    full_extraction_path_on_server = default_storage.path(extraction_game_dir_segment)
                    if os.path.exists(full_extraction_path_on_server) and os.path.isdir(full_extraction_path_on_server):
                        shutil.rmtree(full_extraction_path_on_server)
                        print(f"Çıkarılmış oyun dosyaları silindi: {full_extraction_path_on_server}")
                    else:
                        print(f"Çıkarılmış oyun klasörü bulunamadı veya bir dosya: {full_extraction_path_on_server}")
                except NotImplementedError:
                    print(f"UYARI: Storage backend'i path metodunu desteklemiyor. Çıkarılmış dosyalar ({extraction_game_dir_segment}) manuel silinmeli.")
                except Exception as e_path:
                    print(f"Çıkarılmış oyun klasör yolu alınırken hata: {e_path}")

            except Exception as e:
                print(f"Çıkarılmış oyun dosyaları ({entry_point_full_path} civarı) silinirken hata: {e}")

    def retrieve(self, request, *args, **kwargs):
        """
        Bir oyunun detayları getirildiğinde view_count'u artırır.
        """
        instance = self.get_object()  # İzin kontrolü ve obje getirme burada yapılır.
        Game.objects.filter(pk=instance.id).update(view_count=F('view_count') + 1)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    # --- Özel Aksiyonlar (Rating ve Reporting) ---

    @action(detail=True, methods=['post'], url_path='rate')  # url_path'i değiştirdim
    def rate_game(self, request, id=None):  # lookup_field 'id' olduğu için parametre 'id'
        """
        Belirli bir oyuna oy vermek (like/dislike) veya oyu güncellemek için.
        POST isteği ile body'de {"rating_type": 1} (like için) veya {"rating_type": -1} (dislike için) beklenir.
        """
        game = self.get_object()
        user = request.user

        try:
            rating_type_str = request.data.get('rating_type')
            if rating_type_str is None:
                return Response(
                    {"error": "rating_type alanı zorunludur."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            rating_type = int(rating_type_str)
            if rating_type not in [Rating.RatingChoices.LIKE, Rating.RatingChoices.DISLIKE]:
                raise ValueError("Geçersiz rating_type değeri.")
        except (ValueError, TypeError):
            return Response(
                {"error": "rating_type alanı integer olarak (1 veya -1) gönderilmelidir."},
                status=status.HTTP_400_BAD_REQUEST
            )

        rating_obj, created = Rating.objects.update_or_create(
            user=user, game=game,
            defaults={'rating_type': rating_type}
        )

        serializer = RatingSerializer(rating_obj, context={'request': request})  # context ekledim
        action_taken = "oluşturuldu" if created else "güncellendi"
        return Response(
            {
                "message": f"Oyun için oyunuz başarıyla {action_taken}.",
                "rating": serializer.data
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

    @action(detail=True, methods=['delete'], url_path='unrate')  # url_path'i değiştirdim
    def unrate_game(self, request, id=None):  # lookup_field 'id' olduğu için parametre 'id'
        """
        Kullanıcının belirli bir oyuna verdiği oyu silmek için.
        """
        game = self.get_object()
        user = request.user

        try:
            rating_to_delete = Rating.objects.get(user=user, game=game)
            rating_to_delete.delete()  # Signal burada tetiklenip sayaçları güncellemeli
            return Response(
                {"message": "Oyunuz başarıyla kaldırıldı."},
                status=status.HTTP_204_NO_CONTENT
            )
        except Rating.DoesNotExist:
            return Response(
                {"error": "Bu oyuna verilmiş bir oyunuz bulunmamaktadır."},
                status=status.HTTP_404_NOT_FOUND
            )
        
    @action(detail=True, methods=['post'], url_path='report')  # url_path'i değiştirdim
    def report_game(self, request, id=None):  # lookup_field 'id' olduğu için parametre 'id'
        """
        Belirli bir oyunu raporlamak için.
        POST isteği ile body'de {"reason": "BUG", "description": "Optional details..."} beklenir.
        """
        game = self.get_object()
        user = request.user

        serializer = ReportSerializer(data=request.data, context={'request': request})  # context ekledim
        if serializer.is_valid():
            serializer.save(reporter=user, game=game)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)