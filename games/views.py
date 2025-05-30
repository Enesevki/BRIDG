from django.shortcuts import render

# Create your views here.

# backend/games/views.py

from rest_framework import viewsets, permissions, status
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser  # Dosya yüklemeleri için
from django.db.models import F, Q, Count  # Count ve Q'yu import etmeyi unutmayın
from django_filters.rest_framework import DjangoFilterBackend  # Django Filter backend
from rest_framework import filters  # DRF'nin kendi filtreleri
from .models import Game, Genre, Tag  # Model importları
from .serializers import (  # Serializer importları
    GameSerializer, GenreSerializer, TagSerializer, GameUpdateSerializer, MyGameAnalyticsSerializer
)
from .filters import GameFilter  # Kendi filter'ımızı import edelim
from .utils import FilterValidationMixin  # Custom utils import
from django.core.files.storage import default_storage
import os
import shutil
from .permissions import IsOwnerOrReadOnly  # Yeni izin sınıfımız

# Rate limiting imports (simplified)
from gamehost_project.rate_limiting import rate_limit

# interactions uygulamasının modellerini ve serializer'larını import et
from interactions.models import Rating, Report
from interactions.serializers import RatingSerializer, ReportSerializer

import logging

logger = logging.getLogger(__name__)

class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Genre.objects.all().order_by('name')
    serializer_class = GenreSerializer
    permission_classes = [permissions.AllowAny]


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all().order_by('name')
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]


class GameViewSet(FilterValidationMixin, viewsets.ModelViewSet):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    lookup_field = 'id'  # Primary key alanımızın adı 'id' olduğu için

    # Filtering, Search, and Ordering
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = GameFilter
    search_fields = ['title', 'description', 'creator__username']
    ordering_fields = ['created_at', 'updated_at', 'title', 'likes_count', 'dislikes_count', 'play_count', 'view_count']
    ordering = ['-created_at']  # Default ordering

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
    
    @rate_limit(requests_per_hour=5, key_type='user')  # 5 uploads per hour per user
    def create(self, request, *args, **kwargs):
        """
        Oyun yükleme işlemi - Rate limited.
        """
        # Oyun başlığını ve isteği yapan kullanıcıyı al
        # request.data dosya yüklemelerinde QueryDict olabilir, .get() ile almak daha güvenli.
        title = request.data.get('title')
        creator = request.user  # IsAuthenticated izninden dolayı request.user dolu olmalı

        # Eğer bu başlıkla bu kullanıcıya ait bir oyun zaten varsa, hata döndür
        if title and Game.objects.filter(creator=creator, title=title.strip()).exists():
            response = Response(
                {"title": ["Bu başlıkla zaten bir oyununuz mevcut. Farklı bir başlık seçin."]},
                status=status.HTTP_400_BAD_REQUEST
            )
            return response
        
        # Mükerrer değilse, serializer validation ve creation
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        response = Response(serializer.data, status=status.HTTP_201_CREATED)
        return response

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
        instance = self.get_object() # İzin kontrolü ve obje getirme burada yapılır.
                                     # IsOwnerOrReadOnly izni, yayınlanmamış oyunlar için
                                     # doğru kullanıcıların erişimini sağlar.
        
        # Sadece yayınlanmış oyunlar için veya oyunun sahibi görüntülüyorsa view_count artırılabilir.
        # Veya her detay görüntülemede artırılabilir, bu sizin tercihinize bağlı.
        # Şimdilik, get_object başarılı olduysa (yani kullanıcı görme yetkisine sahipse) artırıyoruz.
        Game.objects.filter(pk=instance.id).update(view_count=F('view_count') + 1)
        
        # Ancak serializer zaten güncel (güncellemeden önceki) instance'ı kullanacak.
        # Eğer güncel view_count'u hemen yanıtta istiyorsak:
        instance.refresh_from_db(fields=['view_count'])

        serializer = self.get_serializer(instance) # Artık action'a göre doğru serializer'ı getirecek
        return Response(serializer.data)

    # --- Özel Aksiyonlar (Rating ve Reporting) ---

    @action(detail=True, methods=['post'], url_path='rate')
    @rate_limit(requests_per_hour=100, key_type='user')  # 100 ratings per hour per user
    def rate_game(self, request, id=None):
        """
        Oyuna puan verme endpoint'i.
        """
        game = self.get_object()
        
        # ✅ Sadece yayınlanmış oyunlara puan verilebilir
        if not game.is_published:
            return Response(
                {"error": "Sadece yayınlanmış oyunlara puan verilebilir."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if game.creator == request.user:
            return Response(
                {"error": "Kendi oyununuza puan veremezsiniz."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rating_type = request.data.get('rating_type')
        
        # ✅ Rating choices validation (1=LIKE, -1=DISLIKE)
        if rating_type not in [Rating.RatingChoices.LIKE, Rating.RatingChoices.DISLIKE]:
            return Response(
                {"error": "rating_type 1 (like) veya -1 (dislike) olmalıdır."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Daha önce verilen puanı kontrol et
        existing_rating, created = Rating.objects.get_or_create(
            user=request.user,
            game=game,
            defaults={'rating_type': rating_type}
        )
        
        if not created:
            # Zaten bir puan verilmiş
            if existing_rating.rating_type == rating_type:
                rating_display = "like" if rating_type == Rating.RatingChoices.LIKE else "dislike"
                return Response(
                    {"message": f"Bu oyuna zaten {rating_display} verdiniz."},
                    status=status.HTTP_200_OK
                )
            else:
                # Farklı bir puan tipi, güncelle
                existing_rating.rating_type = rating_type
                existing_rating.save()
                rating_display = "like" if rating_type == Rating.RatingChoices.LIKE else "dislike"
                return Response(
                    {"message": f"Oyun puanınız {rating_display} olarak güncellendi."},
                    status=status.HTTP_200_OK
                )
        else:
            # Yeni puan oluşturuldu
            rating_display = "like" if rating_type == Rating.RatingChoices.LIKE else "dislike"
            return Response(
                {"message": f"Oyuna {rating_display} verdiniz."},
                status=status.HTTP_201_CREATED
            )

    @action(detail=True, methods=['delete'], url_path='unrate')
    @rate_limit(requests_per_hour=100, key_type='user')  # 100 unrate operations per hour per user  
    def unrate_game(self, request, id=None):
        """
        Oyundan puanı kaldırma endpoint'i.
        """
        game = self.get_object()
        
        # ✅ Sadece yayınlanmış oyunlardan puan kaldırılabilir
        if not game.is_published:
            return Response(
                {"error": "Sadece yayınlanmış oyunlardan puan kaldırılabilir."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            rating = Rating.objects.get(user=request.user, game=game)
            rating.delete()
            return Response(
                {"message": "Oyun puanınız kaldırıldı."},
                status=status.HTTP_200_OK
            )
        except Rating.DoesNotExist:
            return Response(
                {"error": "Bu oyuna henüz puan vermemişsiniz."},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='report')
    @rate_limit(requests_per_hour=20, key_type='user')  # 20 reports per hour per user
    def report_game(self, request, id=None):
        """
        Oyunu şikayet etme endpoint'i.
        """
        game = self.get_object()
        
        # ✅ Sadece yayınlanmış oyunlar şikayet edilebilir
        if not game.is_published:
            return Response(
                {"error": "Sadece yayınlanmış oyunlar şikayet edilebilir."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if game.creator == request.user:
            return Response(
                {"error": "Kendi oyununuzu şikayet edemezsiniz."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', '').strip()
        
        if not reason:
            return Response(
                {"error": "Şikayet sebebi belirtilmelidir."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Daha önce şikayet edilmiş mi kontrol et
        existing_report = Report.objects.filter(user=request.user, game=game).first()
        
        if existing_report:
            return Response(
                {"error": "Bu oyunu daha önce şikayet etmişsiniz."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Yeni şikayet oluştur
        Report.objects.create(user=request.user, game=game, reason=reason)
        
        return Response(
            {"message": "Oyun şikayetiniz kaydedildi."},
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny], url_path='increment_play_count')
    @rate_limit(requests_per_hour=300, key_type='ip')  # 300 play count increments per hour per IP
    def increment_play_count(self, request, id=None):
        """
        Oyunun oynanma sayısını arttırma endpoint'i.
        """
        game = self.get_object()
        
        # Oyunun oynanma sayısını arttır
        game.play_count = F('play_count') + 1
        game.save(update_fields=['play_count'])
        
        # Güncellenmiş oyun objesi için refresh gerekli
        game.refresh_from_db(fields=['play_count'])
        
        return Response(
            {"message": "Oynanma sayısı güncellendi.", "play_count": game.play_count},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated], url_path='my-liked')
    @rate_limit(requests_per_hour=200, key_type='user')  # 200 requests per hour per user
    def my_liked_games(self, request):
        """
        Kullanıcının beğendiği oyunları getiren endpoint.
        """
        if not request.user.is_authenticated:
            return Response(
                {"error": "Bu endpoint için giriş yapmalısınız."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Kullanıcının beğendiği oyunları bul
        user = request.user
        liked_ratings = Rating.objects.filter(user=user, rating_type=Rating.RatingChoices.LIKE)
        liked_games = [rating.game for rating in liked_ratings]
        
        # Sayfalama uygula
        page = self.paginate_queryset(liked_games)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(liked_games, many=True)
        return Response(serializer.data)

class MyGamesAnalyticsListView(generics.ListAPIView):
    """
    Giriş yapmış kullanıcının kendi yüklediği oyunların
    temel analitiklerini listeler.
    """
    serializer_class = MyGameAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated] # Sadece giriş yapmış kullanıcılar

    def get_queryset(self):
        """
        Bu view sadece isteği yapan kullanıcıya ait oyunları döndürmelidir.
        """
        user = self.request.user
        return Game.objects.filter(creator=user).order_by('-created_at')