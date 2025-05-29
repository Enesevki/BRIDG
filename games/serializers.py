# backend/games/serializers.py

from rest_framework import serializers
from .models import Genre, Tag, Game
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.templatetags.static import static  # <--- BU SATIRI EKLEYİN
from django.conf import settings  # MEDIA_URL ve STATIC_URL için (settings.DEBUG kontrolü için de kullanılabilir)
from django.core.files.storage import default_storage
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
    entry_point_url = serializers.SerializerMethodField()  # Oyunun oynanabilir URL'si

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
            'is_published', 'created_at', 'updated_at',
            'likes_count', 'dislikes_count', 'play_count', 'view_count',
        ]
        read_only_fields = [
            'id', 'creator', 'created_at', 'updated_at',
            'likes_count', 'dislikes_count', 'play_count', 'view_count',
            'thumbnail_url', 'game_file_url', 'entry_point_path', 'entry_point_url',
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
                    return full_url # S3 gibi durumlarda zaten tam URL dönebilir
                return full_url
            except Exception:  # URL oluşturulamazsa (örn: dosya yok)
                return None
        return None

    def validate_webgl_build_zip(self, value):
        if value is None:
            return value
        
        # 1. Dosya Boyutu Kontrolü
        max_size_bytes = settings.MAX_GAME_ZIP_SIZE_MB * 1024 * 1024
        if value.size > max_size_bytes:
            raise serializers.ValidationError(
                f"Yüklenen ZIP dosyasının boyutu {settings.MAX_GAME_ZIP_SIZE_MB} MB'ı aşamaz. "
                f"Sizin dosyanızın boyutu: {value.size // (1024 * 1024)} MB."
            )
        
        # 2. Diğer ZIP içeriği doğrulamaları 
        potential_root_folder = None
        has_index = False
        has_build_folder = False
        has_template_data_folder = False

        try:
            value.seek(0)  # Dosya pointer'ını başa al, size kontrolünden sonra okunabilmesi için
            with zipfile.ZipFile(value, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                common_prefix = os.path.commonprefix(file_list)

                if not file_list:
                    raise serializers.ValidationError("Yüklenen ZIP dosyası boş.")

                if common_prefix and common_prefix.endswith('/'):
                    potential_root_folder = common_prefix
                elif common_prefix and '/' in common_prefix:
                    potential_root_folder = os.path.dirname(common_prefix) + '/'
                    if not all(
                        f.startswith(potential_root_folder)
                        for f in file_list if potential_root_folder
                    ):
                        potential_root_folder = ""
                else:
                    potential_root_folder = ""

                expected_index = potential_root_folder + 'index.html'
                expected_build = potential_root_folder + 'Build/'
                expected_template = potential_root_folder + 'TemplateData/'

                has_index = expected_index in file_list
                has_build_folder = any(
                    f.startswith(expected_build) for f in file_list
                )
                has_template_data_folder = any(
                    f.startswith(expected_template) for f in file_list
                )

                if not has_index:
                    raise serializers.ValidationError(
                        f"Zip dosyası '{expected_index}' dosyasını içermelidir."
                    )
                if not has_build_folder:
                    raise serializers.ValidationError(
                        f"Zip dosyası '{expected_build}' klasörünü içermelidir."
                    )
                if not has_template_data_folder:
                    raise serializers.ValidationError(
                        f"Zip dosyası '{expected_template}' klasörünü içermelidir."
                    )

                for member_name in file_list:
                    relative_member_name = member_name
                    if potential_root_folder and member_name.startswith(
                        potential_root_folder
                    ):
                        relative_member_name = member_name[len(potential_root_folder):]
                    if relative_member_name.startswith('/') or '..' in relative_member_name:
                        raise serializers.ValidationError(
                            f"Zip dosyası geçersiz bir göreli dosya yolu içeriyor: '{member_name}'."
                        )
        except zipfile.BadZipFile:
            raise serializers.ValidationError(
                "Yüklenen dosya geçerli bir ZIP dosyası değil."
            )
        except serializers.ValidationError:
            raise
        except Exception as e:
            raise serializers.ValidationError(
                f"ZIP dosyası doğrulanırken bir hata oluştu: {str(e)}"
            )
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

            self._process_uploaded_zip(instance)  # Yeni zip'i işle
        
        # İsteğe bağlı: Eğer thumbnail silinmek isteniyorsa (null gönderildiyse) veya yeni bir tane yüklendiyse
        # bu da burada ele alınabilir. ModelSerializer bunu kısmen halleder.

        return instance

    def _process_uploaded_zip(self, game_instance):
        """
        Processes the uploaded ZIP file for a game instance.
        Extracts the contents of the ZIP file and saves them to the server's storage.
        Updates the game's entry point path based on the extracted files.
        """
        zip_file_field = game_instance.webgl_build_zip
        if not zip_file_field or not zip_file_field.name:
            game_instance.moderation_status = Game.ModerationStatusChoices.CHECKS_FAILED
            game_instance.save(update_fields=['moderation_status'])
            return
        
        # Başarılı bir şekilde çıkarılırsa CHECKS_PASSED olacak,
        # hata olursa CHECKS_FAILED olacak.
        # Bu metot validasyondan sonra çağrıldığı için zip'in temel yapısının
        # (index.html, Build, TemplateData) doğru olduğu varsayılır.
        # Boyut kontrolü de validasyonda yapıldı.

        try:
            game_uuid_str = str(game_instance.id)
            extraction_base_dir = os.path.join('game_builds', 'extracted')
            extraction_target_root_on_server = os.path.join(extraction_base_dir, game_uuid_str)
            root_folder_in_zip = ""
            
            with default_storage.open(zip_file_field.name, 'rb') as f_zip:
                with zipfile.ZipFile(f_zip, 'r') as zip_ref:
                    file_list = zip_ref.namelist()
                    if not file_list:  # Bu validasyonda yakalanmalıydı
                        game_instance.moderation_status = Game.ModerationStatusChoices.CHECKS_FAILED
                        game_instance.save(update_fields=['moderation_status'])
                        return
                    common_prefix = os.path.commonprefix(file_list)
                    if common_prefix and common_prefix.endswith('/'): root_folder_in_zip = common_prefix
                    elif common_prefix and '/' in common_prefix:
                        root_folder_in_zip = os.path.dirname(common_prefix) + '/'
                        if not all(fl.startswith(root_folder_in_zip) for fl in file_list if root_folder_in_zip): root_folder_in_zip = ""
                    else: root_folder_in_zip = ""
                    for member_name_in_zip in file_list:
                        relative_member_name_after_root = member_name_in_zip
                        if root_folder_in_zip and member_name_in_zip.startswith(root_folder_in_zip): relative_member_name_after_root = member_name_in_zip[len(root_folder_in_zip):]
                        if relative_member_name_after_root.startswith('/') or '..' in relative_member_name_after_root: continue
                        target_file_path_on_server = os.path.join(extraction_target_root_on_server, relative_member_name_after_root)
                        if not member_name_in_zip.endswith('/'):
                            file_data = zip_ref.read(member_name_in_zip)
                            default_storage.save(target_file_path_on_server, ContentFile(file_data))
            
            game_instance.entry_point_path = os.path.join(extraction_target_root_on_server, root_folder_in_zip + 'index.html')
            game_instance.moderation_status = Game.ModerationStatusChoices.CHECKS_PASSED  # Veya PENDING_REVIEW
            game_instance.save(update_fields=['entry_point_path', 'moderation_status'])
            print(f"Oyun {game_instance.id} için dosyalar başarıyla işlendi. Moderasyon durumu: {game_instance.moderation_status}")

        except Exception as e:
            print(f"HATA (çıkarma): Zip dosyası {zip_file_field.name} işlenirken hata: {str(e)}")
            game_instance.moderation_status = Game.ModerationStatusChoices.CHECKS_FAILED
            # entry_point_path'i null yapmak veya boşaltmak da iyi bir fikir olabilir
            game_instance.entry_point_path = None
            game_instance.save(update_fields=['moderation_status', 'entry_point_path'])
            # Burada bir hata fırlatmak yerine durumu kaydedip adminin incelemesini bekleyebiliriz.
            # Veya oyunu tamamen silebiliriz (önceki yaklaşımlarda olduğu gibi).
            # Şimdilik CHECKS_FAILED olarak işaretliyoruz.