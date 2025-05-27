from django.shortcuts import render

# Create your views here.

# backend/games/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action  # Özel aksiyonlar için
from django.db.models import F, Count, Q  # F: Field referansı, Count: Aggregation için
from .models import Game, Genre, Tag  # Genre ve Tag'i de import etmeyi unutmayın
from .serializers import GameSerializer, GenreSerializer, TagSerializer  # Genre ve Tag serializerlarını da
import os # Gerekli olabilir (ama serializer'da kullanıldı)
from django.conf import settings # Gerekli olabilir (ama serializer'da kullanıldı)
# zipfile, default_storage, ContentFile importları artık view'da doğrudan gerekmeyebilir,
# çünkü dosya işleme mantığı serializer'a taşındı. Ancak parse ediciler için kalabilir.
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser  # Dosya yüklemeleri için

# interactions uygulamasının serializer'ını ve modelini import et
from interactions.models import Rating, Report  # Rating ve Report modellerini import et
from interactions.serializers import RatingSerializer, ReportSerializer  # Rating ve Report serializerlarını import et


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
    queryset = Game.objects.all().order_by('-created_at')  # Şimdilik tüm oyunlar
    serializer_class = GameSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # Dosya yüklemelerini (multipart/form-data) desteklemek için
    lookup_field = 'id'

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
            self.permission_classes = [permissions.IsAdminUser]  # Veya kendi IsOwner izniniz
        else:  # list, retrieve
            self.permission_classes = [permissions.AllowAny]  # Oyun listesi ve detayı herkese açık
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

    queryset = Game.objects.all().annotate( # Annotate ile like/dislike sayılarını ekleyelim
        likes_count_calculated=Count('ratings', filter=Q(ratings__rating_type=Rating.RatingChoices.LIKE)),
        dislikes_count_calculated=Count('ratings', filter=Q(ratings__rating_type=Rating.RatingChoices.DISLIKE))
    ).order_by('-created_at')
    # NOT: likes_count ve dislikes_count modelde zaten var.
    # Eğer bunları signal ile güncelliyorsak annotate'e gerek yok.
    # Eğer signal kullanmıyorsak ve anlık sayım istiyorsak annotate kullanılabilir
    # veya serializer'da SerializerMethodField ile hesaplanabilir.
    # Şimdilik modeldeki alanları kullanacağız ve signal ile güncelleyeceğiz. Bu yüzden annotate'i yorumlayalım.
    # queryset = Game.objects.all().order_by('-created_at') # Önceki haline geri dönelim

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def rate_game(self, request, id=None):
        """
        Belirli bir oyuna oy vermek (like/dislike) veya oyu güncellemek için.
        POST isteği ile body'de {"rating_type": 1} (like için) veya {"rating_type": -1} (dislike için) beklenir.
        """
        game = self.get_object()  # pk ile belirtilen Game objesini getirir
        user = request.user

        try:
            rating_type = int(request.data.get('rating_type'))
            if rating_type not in [Rating.RatingChoices.LIKE, Rating.RatingChoices.DISLIKE]:
                return Response(
                    {"error": "Geçersiz rating_type. Sadece 1 (Like) veya -1 (Dislike) kabul edilir."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {"error": "rating_type alanı integer olarak (1 veya -1) gönderilmelidir."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Kullanıcının bu oyuna daha önce verdiği bir oy var mı kontrol et, varsa güncelle, yoksa oluştur.
        # update_or_create, unique_together kısıtlamasıyla iyi çalışır.
        rating_obj, created = Rating.objects.update_or_create(
            user=user, game=game,
            defaults={'rating_type': rating_type}  # Eğer yeni oluşturuluyorsa veya güncelleniyorsa bu değeri ata
        )

        serializer = RatingSerializer(rating_obj)  # Oluşturulan/güncellenen Rating objesini serialize et

        # Yanıtı oluştur
        action_taken = "oluşturuldu" if created else "güncellendi"
        return Response(
            {
                "message": f"Oyun için oyunuz başarıyla {action_taken}.",
                "rating": serializer.data
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated], url_path='unrate_game')
    def unrate_game(self, request, id=None):
        """
        Kullanıcının belirli bir oyuna verdiği oyu silmek için.
        """
        game = self.get_object()
        user = request.user

        try:
            rating_to_delete = Rating.objects.get(user=user, game=game)
            rating_to_delete.delete()
            return Response(
                {"message": "Oyunuz başarıyla kaldırıldı."},
                status=status.HTTP_204_NO_CONTENT  # Başarılı silme, içerik yok
            )
        except Rating.DoesNotExist:
            return Response(
                {"error": "Bu oyuna verilmiş bir oyunuz bulunmamaktadır."},
                status=status.HTTP_404_NOT_FOUND
            )
        
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated], url_path='report_game')
    def report_game(self, request, id=None): # lookup_field 'id' ise parametre 'id' olmalı
        """
        Belirli bir oyunu raporlamak için.
        POST isteği ile body'de {"reason": "BUG", "description": "Optional details..."} beklenir.
        """
        game = self.get_object() # id ile belirtilen Game objesini getirir
        user = request.user

        # Gelen veriyi ReportSerializer ile doğrula ve kaydet
        # 'game' ve 'reporter' alanlarını context veya initial_data ile göndermemiz lazım
        # ya da serializer.save() içinde göndereceğiz.
        # En temizi, serializer'da bu alanları read_only yapıp save() içinde göndermek.
        # Game zaten URL'den geliyor, reporter da request.user.

        serializer = ReportSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # reporter'ı ve game'i serializer.save() metoduna göndererek ata
            # Eğer serializer'da game ve reporter alanları writeable ise (read_only değilse)
            # ve request.data içinde geliyorsa, burada ayrıca göndermeye gerek yok.
            # Ancak biz game'i URL'den, reporter'ı request.user'dan alıyoruz.
            serializer.save(reporter=user, game=game)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
