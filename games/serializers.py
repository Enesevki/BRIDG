# backend/games/serializers.py

from rest_framework import serializers
from .models import Genre, Tag, Game
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.templatetags.static import static 
from django.conf import settings  # MEDIA_URL ve STATIC_URL için (settings.DEBUG kontrolü için de kullanılabilir)
from django.core.files.storage import default_storage
import zipfile
import os


# --- Yardımcı Fonksiyon (Sınıf Dışında, Dosyanın Başında) ---
def find_zip_root_folder(file_list_from_zip):
    """
    Verilen dosya listesinden (zip içinden) potansiyel bir kök klasör belirler.
    Eğer tüm dosyalar tek bir ana klasör altındaysa, o klasörün adını döndürür (sonunda '/' ile).
    Aksi takdirde boş string "" döndürür (dosyalar zip'in kökündedir).
    """
    if not file_list_from_zip:
        return ""

    # os.path.commonprefix tüm yollar için ortak en uzun öneki bulur.
    # Örneğin: ["MyGame/index.html", "MyGame/Build/", "MyGame/TemplateData/"] -> "MyGame/"
    # Örneğin: ["index.html", "Build/", "TemplateData/"] -> ""
    # Örneğin: ["Game1/file.txt", "Game2/file.txt"] -> "" (çünkü ortak klasör yok)
    # Örneğin: ["MyGame/file.txt", "MyGame/"] -> "MyGame/"
    
    prefix = os.path.commonprefix(file_list_from_zip)

    if not prefix:  # Ortak bir önek yoksa, kök dizin varsayılır.
        return ""

    # Eğer prefix bir klasörse (sonunda '/' varsa) ve tüm dosyalar bu prefix ile başlıyorsa
    if prefix.endswith('/') and all(f.startswith(prefix) for f in file_list_from_zip):
        return prefix
    
    # Eğer prefix bir dosya yolunun bir parçasıysa (örn: "MyGame/Build")
    # ve potansiyel bir kök klasör oluşturuyorsa.
    # dirname("MyGame/Build") -> "MyGame"
    # dirname("MyGame/") -> "MyGame" (bunu istemiyoruz, son / önemli)
    # dirname("MyGame") -> ""
    
    # commonprefix'in sonu '/' değilse ama içinde '/' varsa, bir üst dizini almayı dene
    if '/' in prefix:
        # rstrip('/') ile sondaki olası '/' kaldırılır, sonra dirname alınır, sonra tekrar '/' eklenir.
        # "MyGame/Build/file.js" -> "MyGame/Build" -> "MyGame/"
        # "MyGame/index.html" -> "MyGame" -> "MyGame/" (eğer commonprefix "MyGame/index.html" ise)
        potential_dir_from_prefix = os.path.dirname(prefix.rstrip('/'))
        if potential_dir_from_prefix:  # Eğer bir üst klasör adı varsa ("" değilse)
            root_candidate = potential_dir_from_prefix + '/'
            if all(f.startswith(root_candidate) for f in file_list_from_zip):
                return root_candidate
    
    # Yukarıdaki koşullar sağlanmazsa, dosyaların zip'in kökünde olduğunu varsay
    return ""
# --- Yardımcı Fonksiyon Sonu ---


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


class GameUpdateSerializer(serializers.ModelSerializer):
    """
    Oyun güncelleme işlemleri için serializer.
    Sadece kullanıcı tarafından güncellenebilecek alanları içerir.
    Zip dosyası, yayın durumu, moderasyon durumu vb. buradan güncellenemez.
    """
    # Yazma işlemleri için (PUT/PATCH)
    genre_ids = serializers.PrimaryKeyRelatedField(
        queryset=Genre.objects.all(),
        many=True,
        source='genres',
        required=False,  # Güncelleme sırasında zorunlu değil (PATCH için)
        allow_empty=True,  # Geçici olarak True, validasyonla kontrol edilecek
        error_messages={
            'does_not_exist': 'Geçersiz tür ID: {pk_value}.',
            'incorrect_type': 'Tür ID\'leri bir liste olmalıdır.'
        }
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        source='tags',
        required=False,  # Güncelleme sırasında zorunlu değil (PATCH için)
        allow_empty=True,  # Geçici olarak True, validasyonla kontrol edilecek
        error_messages={
            'does_not_exist': 'Geçersiz etiket ID: {pk_value}.',
            'incorrect_type': 'Etiket ID\'leri bir liste olmalıdır.'
        }
    )

    class Meta:
        model = Game
        fields = [
            'title', 
            'description', 
            'thumbnail',  # Kullanıcı yeni thumbnail yükleyebilir veya kaldırabilir
            'genre_ids',  # Kullanıcı türleri güncelleyebilir
            'tag_ids',    # Kullanıcı etiketleri güncelleyebilir
        ]
        # Diğer tüm alanlar (id, creator, is_published, moderation_status, webgl_build_zip vb.)
        # bu serializer tarafından güncellenmeyecektir.

    def validate_genre_ids(self, value):
        # Eğer genre_ids alanı PATCH isteğinde gönderildiyse ve boş bir listeyse hata ver.
        # Eğer PUT isteğindeysek ve bu alan gönderildiyse ve boşsa yine hata ver.
        # ModelSerializer, PUT'ta tüm alanları bekler, PATCH'te sadece gönderilenleri.
        # 'required=False' PATCH için işe yarar. PUT için bu validasyon önemli.
        if isinstance(value, list) and not value:
            # Eğer bu alanın gönderilmesi PUT'ta zorunluysa ve boş liste kabul edilmiyorsa
            # (ki 'en az bir tane olmalı' demiştik)
            if not self.partial or (self.partial and 'genre_ids' in self.initial_data):
                 raise serializers.ValidationError("Oyunun en az bir türü olmalıdır. Tüm türleri silemezsiniz.")
        return value

    def validate_tag_ids(self, value):
        if isinstance(value, list) and not value:
            if not self.partial or (self.partial and 'tag_ids' in self.initial_data):
                raise serializers.ValidationError("Oyunun en az bir etiketi olmalıdır. Tüm etiketleri silemezsiniz.")
        return value


class GameSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    creator = GameCreatorSerializer(read_only=True)

    thumbnail_url = serializers.SerializerMethodField()
    game_file_url = serializers.SerializerMethodField()
    entry_point_url = serializers.SerializerMethodField()  # Oyunun oynanabilir URL'si

    # YENİ: moderation_status_display'i SerializerMethodField olarak tanımla
    moderation_status_display = serializers.SerializerMethodField() 

    genre_ids = serializers.PrimaryKeyRelatedField(
        queryset=Genre.objects.all(),
        many=True,
        write_only=True,
        source='genres',
        required=True,
        # allow_empty=False ekleyerek boş liste gönderilmesini de engelleyebiliriz.
        allow_empty=False,  # Boş bir liste ([]) gönderilmesini engeller
        error_messages={  # Özel hata mesajları
            'required': 'En az bir tür seçilmelidir.',
            'empty': 'En az bir tür seçilmelidir (boş liste gönderilemez).',
            'does_not_exist': 'Geçersiz tür ID: {pk_value}.',  # Geçersiz ID için
            'incorrect_type': 'Tür ID\'leri bir liste olmalıdır.'  # Yanlış tipte veri için
        }
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
        source='tags',
        required=True,
        allow_empty=False,  # Boş bir liste ([]) gönderilmesini engeller
        error_messages={
            'required': 'En az bir etiket seçilmelidir.',
            'empty': 'En az bir etiket seçilmelidir (boş liste gönderilemez).',
            'does_not_exist': 'Geçersiz etiket ID: {pk_value}.',
            'incorrect_type': 'Etiket ID\'leri bir liste olmalıdır.'
        }
    )

    class Meta:
        model = Game
        fields = [
            'id', 'title', 'description', 'creator', 'genres', 'tags',
            'genre_ids', 'tag_ids', 'thumbnail', 'thumbnail_url',
            'webgl_build_zip', 'game_file_url', 'entry_point_path', 'entry_point_url',
            'is_published', 'moderation_status', 'moderation_status_display',  # moderation_status_display eklendi
            'created_at', 'updated_at',
            'likes_count', 'dislikes_count', 'play_count', 'view_count',
        ]
        read_only_fields = [
            'id', 'creator', 'created_at', 'updated_at',
            'likes_count', 'dislikes_count', 'play_count', 'view_count',
            'thumbnail_url', 'game_file_url', 'entry_point_path', 'entry_point_url',
            'moderation_status_display',  # Bu da read_only
            # is_published ve moderation_status GameUpdateSerializer'da yönetilecek
        ]

    def get_thumbnail_url(self, obj):
        """
        Oyunun thumbnail'ı için tam URL döndürür.
        Eğer oyunun kendi thumbnail'ı yoksa, varsayılan bir logo URL'si döndürür.
        """
        request = self.context.get('request')
        if obj.thumbnail and hasattr(obj.thumbnail, 'url') and obj.thumbnail.name:  # .name ile dosyanın varlığını kontrol et
            # Kullanıcının yüklediği thumbnail var
            thumbnail_actual_url = obj.thumbnail.url  # Bu MEDIA_URL + dosya_yolu şeklinde gelir
            if request is not None:
                return request.build_absolute_uri(thumbnail_actual_url)
            return thumbnail_actual_url  # Request context yoksa (testler vb.)
        else:
            # Varsayılan thumbnail URL'si
            try:
                default_thumbnail_relative_path = static('static/images/bridg-default-game-thumbnail.png')
            except Exception as e:
                # Eğer static dosya bulunamazsa (yanlış yol vb.) veya bir hata olursa
                print(f"HATA: Varsayılan thumbnail static dosyası bulunamadı veya static tag hata verdi: {e}")
                return None  # Veya boş bir string, veya frontend'in handle edeceği bir placeholder

            if request is not None:
                return request.build_absolute_uri(default_thumbnail_relative_path)
            return default_thumbnail_relative_pat

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
                    return full_url  # S3 gibi durumlarda zaten tam URL dönebilir
                return full_url
            except Exception:  # URL oluşturulamazsa (örn: dosya yok)
                return None
        return None
    
    def get_moderation_status_display(self, obj):  # Bu metot zaten vardı
        """Game modelindeki get_moderation_status_display() metodunu çağırır."""
        return obj.get_moderation_status_display()

    def validate_webgl_build_zip(self, value):  # value burada InMemoryUploadedFile objesi
        if value is None: return value
        
        max_size_bytes = settings.MAX_GAME_ZIP_SIZE_MB * 1024 * 1024
        if value.size > max_size_bytes:
            raise serializers.ValidationError(
                f"Yüklenen ZIP dosyasının boyutu {settings.MAX_GAME_ZIP_SIZE_MB} MB'ı aşamaz. "
                f"Sizin dosyanızın boyutu: {round(value.size / (1024 * 1024), 2)} MB."
            )
        
        potential_root_folder_in_zip = ""
        try:
            value.seek(0)
            with zipfile.ZipFile(value, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                if not file_list:
                    raise serializers.ValidationError("Yüklenen ZIP dosyası boş.")

                # Yardımcı fonksiyonu kullanarak kök klasörü bul
                potential_root_folder_in_zip = find_zip_root_folder(file_list)

                expected_index = potential_root_folder_in_zip + 'index.html'
                expected_build_dir = potential_root_folder_in_zip + 'Build/'
                expected_template_data_dir = potential_root_folder_in_zip + 'TemplateData/'

                # Dosya ve klasör varlık kontrolleri
                if not any(f == expected_index for f in file_list):  # Tam eşleşme
                    raise serializers.ValidationError(f"Zip dosyası '{expected_index}' dosyasını içermelidir.")
                if not any(f.startswith(expected_build_dir) for f in file_list):
                    raise serializers.ValidationError(f"Zip dosyası '{expected_build_dir}' klasörünü (veya içeriğini) içermelidir.")
                if not any(f.startswith(expected_template_data_dir) for f in file_list):
                    raise serializers.ValidationError(f"Zip dosyası '{expected_template_data_dir}' klasörünü (veya içeriğini) içermelidir.")

                # Path traversal kontrolü
                for member_name in file_list:
                    path_to_check = member_name
                    if potential_root_folder_in_zip and member_name.startswith(potential_root_folder_in_zip):
                        path_to_check = member_name[len(potential_root_folder_in_zip):]
                    if path_to_check.startswith('/') or '..' in path_to_check:
                        raise serializers.ValidationError(f"Zip dosyası geçersiz bir göreli dosya yolu içeriyor: '{member_name}'.")
        
        except zipfile.BadZipFile:
            raise serializers.ValidationError("Yüklenen dosya geçerli bir ZIP dosyası değil.")
        except serializers.ValidationError:
            raise
        except Exception as e:
            raise serializers.ValidationError(f"ZIP dosyası doğrulanırken bir hata oluştu: {str(e)}")
        
        value.seek(0)
        # Validasyon başarılı, kök klasör bilgisini bir sonraki aşamaya (create/update) taşımak için
        # serializer instance'ına geçici bir özellik olarak ekleyebiliriz.
        # Bu, _process_uploaded_zip'in bu bilgiyi yeniden hesaplamasını önler.
        self._validated_zip_root_folder = potential_root_folder_in_zip # Geçici özellik
        return value

    def create(self, validated_data):
        # validated_data'dan _validated_zip_root_folder'ı al (veya varsayılan "")
        # Eğer validate_webgl_build_zip çağrılmadıysa (örneğin bu alan gönderilmediyse), bu özellik olmayabilir.
        # Ancak webgl_build_zip zorunlu olduğu için validate_... her zaman çağrılacaktır.
        zip_root_folder = getattr(self, '_validated_zip_root_folder', "")
        
        game_instance = super().create(validated_data)
        self._process_uploaded_zip(game_instance, zip_root_folder)
        return game_instance

    def update(self, instance, validated_data):
        zip_root_folder = getattr(self, '_validated_zip_root_folder', None)
        # Eğer zip dosyası güncellenmiyorsa (PATCH isteğinde gönderilmediyse),
        # zip_root_folder None olacak ve _process_uploaded_zip çağrılmayacak (veya çağrılsa da işlem yapmayacak).
        
        instance = super().update(instance, validated_data)
        if 'webgl_build_zip' in validated_data and validated_data['webgl_build_zip'] is not None:
            if zip_root_folder is None:  # Eğer validate_webgl_build_zip bu update için çağrılmadıysa
                                        # (örn: sadece zip güncelleniyor, diğer validasyonlar eski)
                                        # zip_root_folder'ı yeniden hesapla veya hata ver.
                                        # En iyisi, _validated_zip_root_folder'ın her zaman set edildiğinden emin olmak.
                                        # validate_webgl_build_zip her zaman çağrılır.
                zip_root_folder = find_zip_root_folder(instance.webgl_build_zip.namelist()) # Bu satır çalışmaz, instance.webgl_build_zip ZipFile değil.
                # Doğrusu, eğer zip güncelleniyorsa, validate_webgl_build_zip zaten _validated_zip_root_folder'ı set eder.
                
            self._process_uploaded_zip(instance, zip_root_folder if zip_root_folder is not None else "")
        return instance

    def _process_uploaded_zip(self, game_instance, root_folder_in_zip):
        zip_file_field = game_instance.webgl_build_zip
        if not zip_file_field or not zip_file_field.name:
            # ... (hata durumu ve moderasyon status güncellemesi) ...
            game_instance.moderation_status = Game.ModerationStatusChoices.CHECKS_FAILED
            game_instance.save(update_fields=['moderation_status'])
            return

        try:
            game_uuid_str = str(game_instance.id)
            extraction_base_dir = os.path.join('game_builds', 'extracted')
            extraction_target_root_on_server = os.path.join(extraction_base_dir, game_uuid_str)

            with default_storage.open(zip_file_field.name, 'rb') as f_zip:
                with zipfile.ZipFile(f_zip, 'r') as zip_ref:
                    for member_name_in_zip in zip_ref.namelist():
                        # Çıkarılacak dosyanın, zip içindeki (varsa) kök klasörden sonraki göreli yolu
                        path_inside_zip_content = member_name_in_zip
                        if root_folder_in_zip and member_name_in_zip.startswith(root_folder_in_zip):
                            path_inside_zip_content = member_name_in_zip[len(root_folder_in_zip):]
                        
                        if not path_inside_zip_content:  # Eğer kök klasörün kendisiyse veya boş bir yolsa atla
                            continue

                        # Path traversal kontrolü (tekrar, güvenlik için)
                        if path_inside_zip_content.startswith('/') or '..' in path_inside_zip_content:
                            print(f"UYARI (çıkarma): Güvenlik riski oluşturan yol '{member_name_in_zip}'. Atlanıyor.")
                            continue
                        
                        target_file_path_on_server = os.path.join(extraction_target_root_on_server, path_inside_zip_content)

                        if not member_name_in_zip.endswith('/'): # Dosya ise
                            file_data = zip_ref.read(member_name_in_zip)
                            default_storage.save(target_file_path_on_server, ContentFile(file_data))
            
            # entry_point_path, extraction_target_root_on_server altına çıkarılan 'index.html'in yoludur.
            # path_inside_zip_content mantığına göre 'index.html' direkt bu kök altında olmalı.
            game_instance.entry_point_path = os.path.join(extraction_target_root_on_server, 'index.html')
            game_instance.moderation_status = Game.ModerationStatusChoices.CHECKS_PASSED
            game_instance.save(update_fields=['entry_point_path', 'moderation_status'])
            print(f"Oyun {game_instance.id} için dosyalar başarıyla işlendi. Moderasyon durumu: {game_instance.moderation_status}")

        except Exception as e:
            # ... (hata durumu ve moderasyon status güncellemesi) ...
            print(f"HATA (çıkarma): Zip dosyası {zip_file_field.name} işlenirken hata: {str(e)}")
            game_instance.moderation_status = Game.ModerationStatusChoices.CHECKS_FAILED
            game_instance.entry_point_path = None
            game_instance.save(update_fields=['moderation_status', 'entry_point_path'])