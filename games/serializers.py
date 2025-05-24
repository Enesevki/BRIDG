# backend/games/serializers.py

from rest_framework import serializers
from .models import Genre, Tag, Game # Modellerimizi import ediyoruz
from django.contrib.auth.models import User # User modelini import ediyoruz (Game creator için)


class GenreSerializer(serializers.ModelSerializer):
    """
    Genre modeli için serializer.
    Modelin tüm alanlarını JSON'a dönüştürür.
    """
    class Meta:
        model = Genre
        fields = ['id', 'name', 'slug']
        # Eğer tüm alanları dahil etmek isterseniz:
        # fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    """
    Tag modeli için serializer.
    Modelin tüm alanlarını JSON'a dönüştürür.
    """
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']
        # fields = '__all__'


class GameCreatorSerializer(serializers.ModelSerializer):
    """
    Oyunun yaratıcısı (User modeli) için basit bir serializer.
    Sadece gerekli bilgileri (id ve username) gösterir.
    """
    class Meta:
        model = User
        fields = ['id', 'username']


class GameSerializer(serializers.ModelSerializer):
    """
    Game modeli için serializer.
    İlişkili modelleri (Genre, Tag, User) daha okunabilir şekilde gösterir.
    """
    # İlişkili Genre'leri ve Tag'leri isimleriyle göstermek için (sadece okunur)
    # 'many=True' çünkü bir oyunun birden fazla genre/tag'ı olabilir.
    genres = GenreSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    # Oyunun yaratıcısını (User) GameCreatorSerializer ile göstermek için (sadece okunur)
    creator = GameCreatorSerializer(read_only=True)

    # Thumbnail ve WebGL build URL'lerini dinamik olarak oluşturmak için SerializerMethodField kullanacağız.
    # Bu, MEDIA_URL ayarınızla birleşerek tam URL'yi oluşturur.
    thumbnail_url = serializers.SerializerMethodField()
    game_file_url = serializers.SerializerMethodField() # WebGL build zip dosyasının URL'si

    class Meta:
        model = Game
        fields = [
            'id',
            'title',
            'description',
            'creator', # GameCreatorSerializer ile gösterilecek
            'genres',  # GenreSerializer ile gösterilecek
            'tags',    # TagSerializer ile gösterilecek
            'thumbnail', # Sadece dosya adını/yolunu verir (POST/PUT için)
            'thumbnail_url', # Tam URL'yi verir (GET için)
            'webgl_build_zip', # Sadece dosya adını/yolunu verir (POST/PUT için)
            'game_file_url', # Orijinal zip dosyasının tam URL'si (GET için)
            # 'entry_point_path', # Bu genellikle API üzerinden doğrudan gösterilmez veya değiştirilmez
            'is_published',
            'created_at',
            'updated_at',
            'likes_count',
            'dislikes_count',
            'play_count',
            'view_count',
        ]
        # Sadece okunur alanlar (API üzerinden doğrudan güncellenemezler)
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'likes_count',
            'dislikes_count', 'play_count', 'view_count',
            'thumbnail_url', 'game_file_url'
            # 'creator' ve ilişkili 'genres', 'tags' zaten yukarıda read_only=True olarak tanımlandı.
        ]

    def get_thumbnail_url(self, obj):
        """
        Game objesinin thumbnail alanı için tam URL döndürür.
        Eğer thumbnail yoksa None döndürür.
        """
        request = self.context.get('request')
        if obj.thumbnail and hasattr(obj.thumbnail, 'url'):
            if request is not None:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None

    def get_game_file_url(self, obj):
        """
        Game objesinin webgl_build_zip alanı için tam URL döndürür.
        Eğer dosya yoksa None döndürür.
        """
        request = self.context.get('request')
        if obj.webgl_build_zip and hasattr(obj.webgl_build_zip, 'url'):
            if request is not None:
                return request.build_absolute_uri(obj.webgl_build_zip.url)
            return obj.webgl_build_zip.url
        return None