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
import logging

# File Security Import - Light & Powerful
from .security import validate_game_upload, FileSecurityError
from .input_validation import (  # NEW: Input validation & sanitization
    TextValidator, DataValidator, FormValidator, InputSecurityError,
    validate_request_data, sanitize_input
)
from users.serializers import UserSerializer  # Import from users app

logger = logging.getLogger(__name__)

# =============================================================================
# Yardımcı Fonksiyon (Validation için)
# =============================================================================

def find_zip_root_folder(file_list):
    """
    ZIP dosyasındaki dosya listesini analiz ederek muhtemel kök klasörü bulur.
    """
    if not file_list:
        return ""
    
    # En yaygın kök klasörü bul
    root_folders = set()
    for file_path in file_list:
        if '/' in file_path:
            root_folder = file_path.split('/')[0] + '/'
            root_folders.add(root_folder)
    
    if len(root_folders) == 1:
        return list(root_folders)[0]
    
    return ""  # Kök klasör yok veya belirsiz

# =============================================================================
# Base Serializers with Input Validation
# =============================================================================

class BaseValidationMixin:
    """Mixin to add input validation to serializers"""
    
    def validate(self, data):
        """Apply comprehensive input validation"""
        try:
            # Get the validation type based on serializer class
            if hasattr(self, 'get_validation_type'):
                validation_type = self.get_validation_type()
                
                # Detect if this is a partial update (PATCH request)
                is_partial = getattr(self, 'partial', False)
                
                data = validate_request_data(data, validation_type, is_partial=is_partial)
            
            # Call parent validation
            data = super().validate(data)
            
            return data
            
        except InputSecurityError as e:
            logger.warning(f"Input validation failed: {e}")
            raise serializers.ValidationError(str(e))


# =============================================================================
# Game-related Serializers
# =============================================================================

class GenreSerializer(serializers.ModelSerializer):
    """Genre serializer with basic validation"""
    class Meta:
        model = Genre
        fields = ['id', 'name', 'slug']


class TagSerializer(serializers.ModelSerializer):
    """Tag serializer with basic validation"""
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class GameSerializer(BaseValidationMixin, serializers.ModelSerializer):
    """
    Oyun oluşturma ve listeleme için serializer - Enhanced with input validation
    """
    creator = UserSerializer(read_only=True)
    genres = GenreSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    
    # Write-only fields for creation
    genre_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True,
        help_text="List of genre IDs to associate with this game"
    )
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True,
        help_text="List of tag IDs to associate with this game"
    )
    
    # Additional computed fields
    game_file_url = serializers.SerializerMethodField()
    entry_point_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Game
        fields = [
            'id', 'title', 'description', 'creator', 'genres', 'tags',
            'webgl_build_zip', 'thumbnail', 'is_published', 'moderation_status',
            'created_at', 'updated_at', 'likes_count', 'dislikes_count',
            'play_count', 'view_count', 'entry_point_path',
            'game_file_url', 'entry_point_url', 'thumbnail_url',
            'genre_ids', 'tag_ids'  # Write-only fields
        ]
        read_only_fields = [
            'id', 'creator', 'created_at', 'updated_at', 'likes_count',
            'dislikes_count', 'play_count', 'view_count', 'entry_point_path',
            'moderation_status'
        ]
    
    def get_validation_type(self):
        """Return validation type for BaseValidationMixin"""
        return 'game'
    
    def validate_title(self, value):
        """Validate game title with enhanced security"""
        try:
            return TextValidator.validate_game_title(value)
        except InputSecurityError as e:
            raise serializers.ValidationError(str(e))
    
    def validate_description(self, value):
        """Validate game description with enhanced security"""
        try:
            return TextValidator.validate_game_description(value)
        except InputSecurityError as e:
            raise serializers.ValidationError(str(e))
    
    def validate_genre_ids(self, value):
        """Validate genre IDs"""
        try:
            validated_ids = DataValidator.validate_id_list(value, 'genre', max_count=5)
            
            # Check if all genre IDs exist
            existing_genres = Genre.objects.filter(id__in=validated_ids)
            if len(existing_genres) != len(validated_ids):
                existing_ids = [g.id for g in existing_genres]
                invalid_ids = [id for id in validated_ids if id not in existing_ids]
                raise serializers.ValidationError(f"Invalid genre IDs: {invalid_ids}")
            
            return validated_ids
        except InputSecurityError as e:
            raise serializers.ValidationError(str(e))
    
    def validate_tag_ids(self, value):
        """Validate tag IDs"""
        try:
            validated_ids = DataValidator.validate_id_list(value, 'tag', max_count=10)
            
            # Check if all tag IDs exist
            existing_tags = Tag.objects.filter(id__in=validated_ids)
            if len(existing_tags) != len(validated_ids):
                existing_ids = [t.id for t in existing_tags]
                invalid_ids = [id for id in validated_ids if id not in existing_ids]
                raise serializers.ValidationError(f"Invalid tag IDs: {invalid_ids}")
            
            return validated_ids
        except InputSecurityError as e:
            raise serializers.ValidationError(str(e))
    
    def validate_webgl_build_zip(self, value):
        """Enhanced file validation with security checks"""
        if not value:
            return value
        
        # Basic file validation
        if value.size == 0:
            raise serializers.ValidationError("Uploaded file is empty.")
        
        # Apply existing file security validation
        try:
            validate_game_upload(value)
            logger.info(f"File security validation passed for: {value.name}")
            
        except FileSecurityError as e:
            logger.error(f"File security validation failed for {value.name}: {e}")
            raise serializers.ValidationError(f"File security validation failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected file validation error for {value.name}: {e}")
            raise serializers.ValidationError(f"File validation failed: {str(e)}")
        
        # WebGL structure validation
        try:
            # Find root folder in ZIP
            potential_root_folder_in_zip = ""
            value.seek(0)
            with zipfile.ZipFile(value, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                if not file_list:
                    raise serializers.ValidationError("Uploaded ZIP file is empty.")

                potential_root_folder_in_zip = find_zip_root_folder(file_list)

                expected_index = potential_root_folder_in_zip + 'index.html'
                expected_build_dir = potential_root_folder_in_zip + 'Build/'
                expected_template_data_dir = potential_root_folder_in_zip + 'TemplateData/'

                # Check required files and folders
                if not any(f == expected_index for f in file_list):
                    raise serializers.ValidationError(f"ZIP file must contain '{expected_index}'.")
                if not any(f.startswith(expected_build_dir) for f in file_list):
                    raise serializers.ValidationError(f"ZIP file must contain '{expected_build_dir}' folder.")
                if not any(f.startswith(expected_template_data_dir) for f in file_list):
                    raise serializers.ValidationError(f"ZIP file must contain '{expected_template_data_dir}' folder.")

            value.seek(0)
            self._validated_zip_root_folder = potential_root_folder_in_zip
            
        except zipfile.BadZipFile:
            raise serializers.ValidationError("Uploaded file is not a valid ZIP archive.")
        except serializers.ValidationError:
            raise
        except Exception as e:
            raise serializers.ValidationError(f"ZIP file validation error: {str(e)}")
        
        return value
    
    def validate(self, data):
        """Enhanced full form validation"""
        try:
            # Apply comprehensive input validation
            data = super().validate(data)
            
            # Additional business logic validation
            if self.instance:
                # Update validation
                if 'webgl_build_zip' in data and data['webgl_build_zip']:
                    raise serializers.ValidationError(
                        "Game file cannot be updated after initial upload."
                    )
            
            # Check for duplicate titles by the same user
            title = data.get('title')
            if title and hasattr(self, 'context') and 'request' in self.context:
                user = self.context['request'].user
                existing_game = Game.objects.filter(
                    creator=user,
                    title=title
                ).exclude(id=getattr(self.instance, 'id', None))
                
                if existing_game.exists():
                    raise serializers.ValidationError({
                        "title": "You already have a game with this title."
                    })
            
            return data
            
        except InputSecurityError as e:
            raise serializers.ValidationError(str(e))
    
    def get_game_file_url(self, obj):
        """Generate game file URL"""
        if obj.webgl_build_zip:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.webgl_build_zip.url)
        return None
    
    def get_entry_point_url(self, obj):
        """Generate game entry point URL"""
        if obj.entry_point_path:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri('/media/' + obj.entry_point_path)
        return None
    
    def get_thumbnail_url(self, obj):
        """Generate thumbnail URL with fallback to default"""
        thumbnail_url = obj.get_thumbnail_url()
        
        # If it's a relative URL, make it absolute
        request = self.context.get('request')
        if request and not thumbnail_url.startswith(('http://', 'https://')):
            return request.build_absolute_uri(thumbnail_url)
        
        return thumbnail_url
    
    def create(self, validated_data):
        """Create game with M2M relationships and file processing"""
        # Extract M2M data
        genre_ids = validated_data.pop('genre_ids', [])
        tag_ids = validated_data.pop('tag_ids', [])
        
        # Create game instance
        game = Game.objects.create(**validated_data)
        
        # Set M2M relationships
        if genre_ids:
            game.genres.set(genre_ids)
        if tag_ids:
            game.tags.set(tag_ids)
        
        # Process uploaded ZIP file
        zip_root_folder = getattr(self, '_validated_zip_root_folder', "")
        self._process_uploaded_zip(game, zip_root_folder)
        
        logger.info(f"Game created successfully: {game.title} (ID: {game.id})")
        return game
    
    def _process_uploaded_zip(self, game_instance, root_folder_in_zip):
        """Process uploaded ZIP file and extract game contents"""
        zip_file_field = game_instance.webgl_build_zip
        if not zip_file_field or not zip_file_field.name:
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
                        # Get relative path inside ZIP content
                        path_inside_zip_content = member_name_in_zip
                        if root_folder_in_zip and member_name_in_zip.startswith(root_folder_in_zip):
                            path_inside_zip_content = member_name_in_zip[len(root_folder_in_zip):]
                        
                        if not path_inside_zip_content:  # Skip root folder itself
                            continue

                        # Path traversal security check
                        if path_inside_zip_content.startswith('/') or '..' in path_inside_zip_content:
                            logger.warning(f"Security risk path '{member_name_in_zip}'. Skipping.")
                            continue
                        
                        target_file_path_on_server = os.path.join(extraction_target_root_on_server, path_inside_zip_content)

                        if not member_name_in_zip.endswith('/'):  # It's a file
                            file_data = zip_ref.read(member_name_in_zip)
                            default_storage.save(target_file_path_on_server, ContentFile(file_data))
            
            # Set entry point path
            game_instance.entry_point_path = os.path.join(extraction_target_root_on_server, 'index.html')
            game_instance.moderation_status = Game.ModerationStatusChoices.CHECKS_PASSED
            
            # ✅ Admin onayı için bekleyecek (is_published manuel olarak ayarlanacak)
            # is_published = False olarak kalacak, admin panelden onaylayacak
            
            game_instance.save(update_fields=['entry_point_path', 'moderation_status'])
            
            logger.info(f"Game {game_instance.id} files processed successfully. Moderation status: {game_instance.moderation_status}. Waiting for admin approval.")

        except Exception as e:
            logger.error(f"ZIP processing error for {zip_file_field.name}: {str(e)}")
            game_instance.moderation_status = Game.ModerationStatusChoices.CHECKS_FAILED
            game_instance.entry_point_path = None
            game_instance.save(update_fields=['moderation_status', 'entry_point_path'])


class GameUpdateSerializer(BaseValidationMixin, serializers.ModelSerializer):
    """
    Oyun güncelleme için serializer - Enhanced validation
    """
    genre_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of genre IDs to associate with this game"
    )
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of tag IDs to associate with this game"
    )
    
    class Meta:
        model = Game
        fields = [
            'title', 'description', 'is_published', 'thumbnail',
            'genre_ids', 'tag_ids'
        ]
    
    def get_validation_type(self):
        """Return validation type for BaseValidationMixin"""
        return 'game'
    
    def validate_title(self, value):
        """Validate game title with enhanced security"""
        try:
            return TextValidator.validate_game_title(value)
        except InputSecurityError as e:
            raise serializers.ValidationError(str(e))
    
    def validate_description(self, value):
        """Validate game description with enhanced security"""
        try:
            return TextValidator.validate_game_description(value)
        except InputSecurityError as e:
            raise serializers.ValidationError(str(e))
    
    def validate_genre_ids(self, value):
        """Validate genre IDs"""
        if not value:
            return value
        
        try:
            validated_ids = DataValidator.validate_id_list(value, 'genre', max_count=5)
            
            # Check if all genre IDs exist
            existing_genres = Genre.objects.filter(id__in=validated_ids)
            if len(existing_genres) != len(validated_ids):
                existing_ids = [g.id for g in existing_genres]
                invalid_ids = [id for id in validated_ids if id not in existing_ids]
                raise serializers.ValidationError(f"Invalid genre IDs: {invalid_ids}")
            
            return validated_ids
        except InputSecurityError as e:
            raise serializers.ValidationError(str(e))
    
    def validate_tag_ids(self, value):
        """Validate tag IDs"""
        if not value:
            return value
        
        try:
            validated_ids = DataValidator.validate_id_list(value, 'tag', max_count=10)
            
            # Check if all tag IDs exist
            existing_tags = Tag.objects.filter(id__in=validated_ids)
            if len(existing_tags) != len(validated_ids):
                existing_ids = [t.id for t in existing_tags]
                invalid_ids = [id for id in validated_ids if id not in existing_ids]
                raise serializers.ValidationError(f"Invalid tag IDs: {invalid_ids}")
            
            return validated_ids
        except InputSecurityError as e:
            raise serializers.ValidationError(str(e))
    
    def validate(self, data):
        """Enhanced update validation"""
        try:
            # Apply comprehensive input validation
            data = super().validate(data)
            
            # Check for duplicate titles
            title = data.get('title')
            if title and self.instance:
                user = self.instance.creator
                existing_game = Game.objects.filter(
                    creator=user,
                    title=title
                ).exclude(id=self.instance.id)
                
                if existing_game.exists():
                    raise serializers.ValidationError({
                        "title": "You already have a game with this title."
                    })
            
            return data
            
        except InputSecurityError as e:
            raise serializers.ValidationError(str(e))
    
    def update(self, instance, validated_data):
        """Update game with M2M relationships"""
        # Extract M2M data
        genre_ids = validated_data.pop('genre_ids', None)
        tag_ids = validated_data.pop('tag_ids', None)
        
        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update M2M relationships if provided
        if genre_ids is not None:
            instance.genres.set(genre_ids)
        if tag_ids is not None:
            instance.tags.set(tag_ids)
        
        logger.info(f"Game updated successfully: {instance.title} (ID: {instance.id})")
        return instance


class MyGameAnalyticsSerializer(serializers.ModelSerializer):
    """
    Kullanıcının kendi oyunları için basit analitik veriler
    """
    genres = GenreSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Game
        fields = [
            'id', 'title', 'is_published', 'moderation_status',
            'created_at', 'updated_at', 'likes_count', 'dislikes_count',
            'play_count', 'view_count', 'genres', 'tags'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
