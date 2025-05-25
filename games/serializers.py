# backend/games/serializers.py

from rest_framework import serializers
from .models import Genre, Tag, Game
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import zipfile
import os


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
    genres = GenreSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    creator = GameCreatorSerializer(read_only=True)

    thumbnail_url = serializers.SerializerMethodField()
    game_file_url = serializers.SerializerMethodField()
    entry_point_url = serializers.SerializerMethodField() # Oyunun oynanabilir URL'si

    genre_ids = serializers.PrimaryKeyRelatedField(
        queryset=Genre.objects.all(),
        many=True, write_only=True, source='genres', required=False
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True, write_only=True, source='tags', required=False
    )

    class Meta:
        model = Game
        fields = [
            'id', 'title', 'description', 'creator', 'genres', 'tags',
            'genre_ids', 'tag_ids', 'thumbnail', 'thumbnail_url',
            'webgl_build_zip', 'game_file_url', 'entry_point_path', 'entry_point_url',
            'is_published', 'created_at', 'updated_at',
            'likes_count', 'dislikes_count', 'play_count', 'view_count',
        ]
        read_only_fields = [
            'id', 'creator', 'created_at', 'updated_at',
            'likes_count', 'dislikes_count', 'play_count', 'view_count',
            'thumbnail_url', 'game_file_url', 'entry_point_path', 'entry_point_url',
        ]

    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and hasattr(obj.thumbnail, 'url'):
            if request is not None:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None

    def get_game_file_url(self, obj):
        request = self.context.get('request')
        if obj.webgl_build_zip and hasattr(obj.webgl_build_zip, 'url'):
            if request is not None:
                return request.build_absolute_uri(obj.webgl_build_zip.url)
            return obj.webgl_build_zip.url
        return None

    def get_entry_point_url(self, obj):
        request = self.context.get('request')
        if obj.entry_point_path:
            # default_storage.url(), MEDIA_URL'i başına ekleyerek tam URL'yi oluşturur.
            try:
                full_url = default_storage.url(obj.entry_point_path)
                if request is not None:
                    # Eğer full_url zaten http ile başlamıyorsa (yerel storage gibi)
                    if not full_url.startswith(('http://', 'https://')):
                         return request.build_absolute_uri(full_url)
                    return full_url # S3 gibi durumlarda zaten tam URL dönebilir
                return full_url
            except Exception: # URL oluşturulamazsa (örn: dosya yok)
                return None
        return None

    def validate_webgl_build_zip(self, value):
        """
        Yüklenen ZIP dosyasının içeriğini doğrular.
        - Geçerli bir zip dosyası mı?
        - İçinde 'index.html' var mı?
        - Güvenli dosya yolları içeriyor mu?
        Bu validasyon, dosya kaydedilmeden *önce* çalışır.
        """
        if value is None: # Eğer dosya isteğe bağlıysa ve gelmediyse
            return value

        try:
            with zipfile.ZipFile(value, 'r') as zip_ref: # value burada InMemoryUploadedFile objesi
                # value.seek(0) # Dosya pointer'ını başa al, eğer daha önce okunduysa
                # Bu satır genellikle InMemoryUploadedFile için gerekli olmaz ama büyük dosyalarda gerekebilir.

                # 1. index.html kontrolü
                if 'index.html' not in zip_ref.namelist():
                    raise serializers.ValidationError("Zip dosyası kök dizininde 'index.html' içermelidir.")

                # 2. Path traversal kontrolü
                for member_name in zip_ref.namelist():
                    if member_name.startswith('/') or '..' in member_name:
                        raise serializers.ValidationError(
                            f"Zip dosyası geçersiz bir dosya yolu içeriyor: '{member_name}'. "
                            "Tüm dosyalar zip kök dizinine göreceli olmalıdır."
                        )
                
                # 3. (İsteğe bağlı) Beklenen klasör yapısı kontrolü (Build/, TemplateData/)
                # required_folders = ['Build/', 'TemplateData/']
                # actual_folders_in_zip = {name for name in zip_ref.namelist() if name.endswith('/')}
                # if not all(folder in actual_folders_in_zip for folder in required_folders):
                #     raise serializers.ValidationError("Zip dosyası 'Build/' ve 'TemplateData/' klasörlerini içermelidir.")

        except zipfile.BadZipFile:
            raise serializers.ValidationError("Yüklenen dosya geçerli bir ZIP dosyası değil.")
        except Exception as e: # Diğer olası hatalar
            raise serializers.ValidationError(f"ZIP dosyası işlenirken bir hata oluştu: {str(e)}")
        
        # Dosya pointer'ını başa almayı unutmayın, böylece Django dosyayı daha sonra kaydedebilir.
        value.seek(0)
        return value

    def create(self, validated_data):
        """
        Game objesini oluşturur ve zip dosyasını işler (çıkarır).
        """
        # 'creator' alanı validated_data'da olmayacak çünkü read_only. View'da atanacak.
        # 'genres' ve 'tags' (ManyToManyField) validated_data'da ID listeleri olarak gelir
        # (source ve PrimaryKeyRelatedField sayesinde). ModelSerializer bunları otomatik işler.

        # webgl_build_zip validasyondan geçti, şimdi normal şekilde kaydedilecek.
        game_instance = super().create(validated_data)

        # Dosya işleme (zip çıkarma) işlemini burada yapıyoruz, çünkü game_instance artık ID'ye sahip.
        self._process_uploaded_zip(game_instance)

        return game_instance

    def update(self, instance, validated_data):
        """
        Game objesini günceller. Eğer yeni bir zip dosyası yüklendiyse onu da işler.
        """
        # Önceki zip ve thumbnail dosyalarını sakla (silme işlemi için gerekebilir)
        # old_zip_path = instance.webgl_build_zip.name if instance.webgl_build_zip else None
        # old_thumbnail_path = instance.thumbnail.name if instance.thumbnail else None

        # ManyToMany alanları (genres, tags) ModelSerializer tarafından halledilir.
        instance = super().update(instance, validated_data)

        # Eğer 'webgl_build_zip' güncelleniyorsa (yani yeni bir zip yüklendiyse)
        if 'webgl_build_zip' in validated_data and validated_data['webgl_build_zip'] is not None:
            # İsteğe bağlı: Önceki çıkarılmış dosyaları silmek gerekebilir.
            # Bu kısım karmaşık olabilir, şimdilik basit tutuyoruz.
            # if instance.entry_point_path and default_storage.exists(os.path.dirname(instance.entry_point_path)):
            #     # Klasörü ve içeriğini silmek için özel bir fonksiyon yazmak gerekebilir.
            #     # default_storage.delete() genellikle tek bir dosyayı siler.
            #     pass

            self._process_uploaded_zip(instance) # Yeni zip'i işle
        
        # İsteğe bağlı: Eğer thumbnail silinmek isteniyorsa (null gönderildiyse) veya yeni bir tane yüklendiyse
        # bu da burada ele alınabilir. ModelSerializer bunu kısmen halleder.

        return instance

    def _process_uploaded_zip(self, game_instance):
        """
        Game instance'ına bağlı webgl_build_zip dosyasını işler, çıkarır
        ve entry_point_path'i günceller.
        Bu metod, create ve update içinde çağrılır.
        """
        zip_file_field = game_instance.webgl_build_zip
        if not zip_file_field or not zip_file_field.name: # Dosya yoksa veya adı boşsa
            # Bu durum normalde validasyonda yakalanmalıydı.
            # Eğer webgl_build_zip isteğe bağlıysa burası atlanabilir.
            # Modelimiz zorunlu tuttuğu için bu bir hata durumudur.
            # Aslında instance.delete() veya bir hata fırlatmak gerekebilir.
            print(f"UYARI: _process_uploaded_zip çağrıldı ama {game_instance.id} için zip dosyası bulunamadı.")
            return

        try:
            game_uuid_str = str(game_instance.id)
            extraction_base_dir = os.path.join('game_builds', 'extracted')
            extraction_path_segment = os.path.join(extraction_base_dir, game_uuid_str) # örn: game_builds/extracted/uuid/

            # Önceki çıkarılmış dosyaları sil (eğer varsa ve update ise)
            # Bu, özellikle update senaryolarında önemlidir.
            # Basit bir yol: tüm klasörü silmeye çalışmak. Daha güvenli yöntemler de var.
            # NOT: default_storage.exists() klasörler için her zaman doğru çalışmayabilir.
            # ve default_storage.delete() klasörleri silmeyebilir.
            # Bu yüzden yerel dosya sistemi için shutil.rmtree gibi bir şey kullanmak gerekebilir,
            # ama bu storage backend bağımlılığı yaratır. Şimdilik bu adımı atlıyoruz veya
            # dosya bazlı silme yapıyoruz (üzerine yazılacağı için gerek olmayabilir).
            # default_storage genellikle aynı yola kaydedince üzerine yazar.

            with default_storage.open(zip_file_field.name, 'rb') as f:
                with zipfile.ZipFile(f, 'r') as zip_ref:
                    for member_name in zip_ref.namelist():
                        if member_name.startswith('/') or '..' in member_name:
                            continue # Path traversal (zaten validasyonda da kontrol edildi)
                        
                        target_file_path = os.path.join(extraction_path_segment, member_name)
                        if member_name.endswith('/'):
                            # Klasörler için bir şey yapmaya gerek yok, dosyalar kaydedilirken oluşur.
                            pass
                        else:
                            file_data = zip_ref.read(member_name)
                            default_storage.save(target_file_path, ContentFile(file_data))
            
            game_instance.entry_point_path = os.path.join(extraction_path_segment, 'index.html')
            game_instance.save(update_fields=['entry_point_path'])

        except Exception as e: # BadZipFile zaten validasyonda yakalandı
            # Bu aşamada bir hata olursa, durum karmaşıklaşır.
            # Belki oyunu 'has_error=True' gibi işaretlemek veya loglamak gerekir.
            # Yüklenen zip dosyasını ve kısmen çıkarılan dosyaları temizlemek de önemlidir.
            print(f"HATA: Zip dosyası {zip_file_field.name} işlenirken (çıkarılırken) hata: {str(e)}")
            # game_instance.is_published = False # Belki yayınlanmamış olarak işaretle
            # game_instance.some_error_field = str(e)
            # game_instance.save()
            # raise serializers.ValidationError({"detail": f"Dosya çıkarma hatası: {str(e)}"})
            # Şimdilik sadece logluyoruz.
            # Eğer bu kritik bir hataysa ve oyunun var olmaması gerekiyorsa,
            # instance.delete() çağrılabilir, ancak bu create/update akışını bozar.
            pass # Veya daha iyi bir hata yönetimi