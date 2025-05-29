from django.shortcuts import render

# Create your views here.

# backend/games/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser  # Dosya yüklemeleri için
from django.db.models import F, Q, Count  # Count ve Q'yu import etmeyi unutmayın
from .models import Game, Genre, Tag  # Model importları
from .serializers import (  # Serializer importları
    GameSerializer, GenreSerializer, TagSerializer  #GameUpdateSerializer
)
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
    parser_classes = [MultiPartParser, FormParser]
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
        '''if self.action in ['update', 'partial_update']:
            return GameUpdateSerializer  # Oyun güncelleme için ayrı serializer'''
        return GameSerializer  # Diğer tüm aksiyonlar için varsayılan

    def get_permissions(self):
        """
        Aksiyon bazlı izinler.
        """
        if self.action == 'create':
            self.permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy', 'retrieve']:
            self.permission_classes = [IsOwnerOrReadOnly]
        elif self.action in ['rate_game', 'unrate_game', 'report_game']:  # Özel aksiyonlarımız için
            self.permission_classes = [permissions.IsAuthenticated]  # Sadece giriş yapmışlar
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
        """
        Bir oyun silindiğinde ilişkili dosyaları da siler.
        """
        # Önce dosyaları silmeye çalış
        # (Bu kısım için default_storage ve os importları dosyanın en başında olmalı)
        # import os
        # from django.core.files.storage import default_storage
        # import shutil

        if instance.webgl_build_zip and default_storage.exists(instance.webgl_build_zip.name):
            default_storage.delete(instance.webgl_build_zip.name)
        if instance.thumbnail and default_storage.exists(instance.thumbnail.name):
            default_storage.delete(instance.thumbnail.name)
        
        if instance.entry_point_path:
            try:
                game_uuid_str = str(instance.id)
                extraction_game_dir_segment = os.path.join('game_builds', 'extracted', game_uuid_str)
                # default_storage.path() yerel dosya sistemi için çalışır,
                # bulut depolama için farklı bir yaklaşım gerekebilir.
                # Şimdilik yerel için varsayalım.
                full_extraction_path_on_server = default_storage.path(extraction_game_dir_segment)

                if os.path.exists(full_extraction_path_on_server) and os.path.isdir(full_extraction_path_on_server):
                    import shutil # Klasör ve içeriğini silmek için
                    shutil.rmtree(full_extraction_path_on_server)
                    print(f"Oyun dosyaları silindi: {full_extraction_path_on_server}")
            except NotImplementedError: # default_storage.path() S3 gibi bazı backends'lerde desteklenmeyebilir
                 print(f"UYARI: Storage backend'i path metodunu desteklemiyor. Çıkarılmış dosyalar ({extraction_game_dir_segment}) manuel silinmeli.")
            except Exception as e:
                print(f"Çıkarılmış oyun dosyaları ({extraction_game_dir_segment}) silinirken hata: {e}")
        
        instance.delete()

    def retrieve(self, request, *args, **kwargs):
        """
        Bir oyunun detayları getirildiğinde view_count'u artırır.
        """
        instance = self.get_object() # İzin kontrolü ve obje getirme burada yapılır.
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