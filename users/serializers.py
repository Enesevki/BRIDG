# backend/users/serializers.py

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password  # Şifre politikalarını kontrol etmek için
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.tokens import RefreshToken
from games.input_validation import (  # Import input validation system
    TextValidator, DataValidator, FormValidator, InputSecurityError,
    validate_request_data, sanitize_input
)
import logging
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


# =============================================================================
# Base Validation Mixin
# =============================================================================

class BaseValidationMixin:
    """Mixin to add input validation to serializers"""
    
    def validate(self, data):
        """Apply comprehensive input validation"""
        try:
            # Get the validation type based on serializer class
            if hasattr(self, 'get_validation_type'):
                validation_type = self.get_validation_type()
                data = validate_request_data(data, validation_type)
            
            # Call parent validation
            data = super().validate(data)
            
            return data
            
        except InputSecurityError as e:
            logger.warning(f"Input validation failed: {e}")
            raise serializers.ValidationError(str(e))


# =============================================================================
# User Serializers with Enhanced Validation
# =============================================================================

class UserSerializer(serializers.ModelSerializer):
    """
    Kullanıcı bilgilerini getirmek için serializer.
    Şifre gibi hassas bilgileri döndürmez.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined']


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Kullanıcı kaydı için serializer.
    Input validation ve güvenlik kontrolleri içerir.
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2']

    def get_validation_type(self):
        """Form validator için validation tipini döndürür."""
        return 'user_registration'

    def validate_username(self, value):
        """Kullanıcı adı validasyonu."""
        # Basic username validation
        if len(value) < 3 or len(value) > 30:
            raise serializers.ValidationError("Kullanıcı adı 3-30 karakter arasında olmalıdır.")
        
        # Allow only alphanumeric and underscore
        if not value.replace('_', '').isalnum():
            raise serializers.ValidationError("Kullanıcı adı sadece harf, rakam ve alt çizgi içerebilir.")
        
        return value

    def validate_email(self, value):
        """Email validasyonu."""
        # Basic email validation (Django will handle detailed validation)
        if '@' not in value or '.' not in value.split('@')[-1]:
            raise serializers.ValidationError("Geçerli bir email adresi girin.")
        
        return value

    def validate_password(self, value):
        """Şifre güvenlik validasyonu."""
        # Django's built-in password validation
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        
        # Additional custom validation
        if len(value) < 8:
            raise serializers.ValidationError("Şifre en az 8 karakter olmalıdır.")
        
        return value

    def validate(self, data):
        """Cross-field validation."""
        # Şifre eşleşme kontrolü
        if data['password'] != data['password2']:
            raise serializers.ValidationError({
                'password2': 'Şifreler eşleşmiyor.'
            })
        
        # Check if username already exists
        if User.objects.filter(username__iexact=data['username']).exists():
            raise serializers.ValidationError({
                'username': 'Bu kullanıcı adı zaten alınmış.'
            })
        
        # Check if email already exists
        if User.objects.filter(email__iexact=data['email']).exists():
            raise serializers.ValidationError({
                'email': 'Bu email adresi zaten kayıtlı.'
            })
        
        return data

    def create(self, validated_data):
        """Yeni kullanıcı oluşturma."""
        # password2'yi çıkar (database'e kaydetmeyeceğiz)
        validated_data.pop('password2')
        
        # Kullanıcıyı oluştur
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        
        return user


class UserProfileSerializer(BaseValidationMixin, serializers.ModelSerializer):
    """User profile serializer for updates"""
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
    
    def get_validation_type(self):
        """Return validation type for BaseValidationMixin"""
        return 'user_profile'
    
    def validate_username(self, value):
        """Validate username for profile updates"""
        try:
            validated_username = TextValidator.validate_username(value)
            
            # Check if username already exists (excluding current user)
            if self.instance:
                existing = User.objects.filter(
                    username__iexact=validated_username
                ).exclude(id=self.instance.id)
                
                if existing.exists():
                    raise serializers.ValidationError("This username is already taken.")
            
            return validated_username
        except InputSecurityError as e:
            raise serializers.ValidationError(str(e))
    
    def validate_email(self, value):
        """Validate email for profile updates"""
        try:
            validated_email = DataValidator.validate_email(value)
            
            # Check if email already exists (excluding current user)
            if self.instance:
                existing = User.objects.filter(
                    email__iexact=validated_email
                ).exclude(id=self.instance.id)
                
                if existing.exists():
                    raise serializers.ValidationError("This email address is already registered.")
            
            return validated_email
        except InputSecurityError as e:
            raise serializers.ValidationError(str(e))
    
    def validate_first_name(self, value):
        """Validate first name"""
        if not value:
            return value
        
        try:
            # Basic text sanitization for names
            cleaned_value = sanitize_input(value, 'text')
            
            if len(cleaned_value) > 50:
                raise serializers.ValidationError("First name cannot exceed 50 characters.")
            
            return cleaned_value
        except InputSecurityError as e:
            raise serializers.ValidationError(str(e))
    
    def validate_last_name(self, value):
        """Validate last name"""
        if not value:
            return value
        
        try:
            # Basic text sanitization for names
            cleaned_value = sanitize_input(value, 'text')
            
            if len(cleaned_value) > 50:
                raise serializers.ValidationError("Last name cannot exceed 50 characters.")
            
            return cleaned_value
        except InputSecurityError as e:
            raise serializers.ValidationError(str(e))
    
    def update(self, instance, validated_data):
        """Update user profile with logging"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        logger.info(f"User profile updated: {instance.username} (ID: {instance.id})")
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """
    Kullanıcı şifre değiştirme için serializer.
    Mevcut şifre doğrulaması ve yeni şifre validasyonu içerir.
    """
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)
    new_password2 = serializers.CharField(write_only=True, required=True, min_length=8)

    def validate_old_password(self, value):
        """Mevcut şifre doğrulaması."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Mevcut şifre yanlış.")
        return value

    def validate_new_password(self, value):
        """Yeni şifre güvenlik validasyonu."""
        user = self.context['request'].user
        
        # Django's built-in password validation
        try:
            validate_password(value, user)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        
        # Additional custom validation
        if len(value) < 8:
            raise serializers.ValidationError("Şifre en az 8 karakter olmalıdır.")
        
        # Mevcut şifre ile aynı olmamalı
        if user.check_password(value):
            raise serializers.ValidationError("Yeni şifre mevcut şifre ile aynı olamaz.")
        
        return value

    def validate(self, data):
        """Cross-field validation."""
        # Yeni şifreler eşleşme kontrolü
        if data['new_password'] != data['new_password2']:
            raise serializers.ValidationError({
                'new_password2': 'Yeni şifreler eşleşmiyor.'
            })
        
        return data

    def save(self, **kwargs):
        """Şifre değiştirme işlemi."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class EmailVerificationSerializer(serializers.Serializer):
    """
    Email doğrulama kodu için serializer.
    """
    code = serializers.CharField(max_length=6, min_length=6, required=True)
    
    def validate_code(self, value):
        """Doğrulama kodu format kontrolü."""
        # Sadece rakam olmalı
        if not value.isdigit():
            raise serializers.ValidationError("Doğrulama kodu sadece rakamlardan oluşmalıdır.")
        
        # 6 haneli olmalı
        if len(value) != 6:
            raise serializers.ValidationError("Doğrulama kodu 6 haneli olmalıdır.")
        
        return value

    def validate(self, data):
        """Kullanıcı ve kod doğrulaması."""
        user = self.context['request'].user
        code = data['code']
        
        # UserProfile'ı kontrol et
        if not hasattr(user, 'profile'):
            raise serializers.ValidationError({
                'non_field_errors': ['Kullanıcı profili bulunamadı.']
            })
        
        profile = user.profile
        
        # Email zaten doğrulanmış mı?
        if profile.email_verified:
            raise serializers.ValidationError({
                'non_field_errors': ['Email adresi zaten doğrulanmış.']
            })
        
        # Kod geçerli mi?
        if not profile.is_verification_code_valid(code):
            attempts_left = max(0, 5 - profile.verification_attempts - 1)
            raise serializers.ValidationError({
                'code': f'Geçersiz veya süresi dolmuş kod. {attempts_left} deneme hakkınız kaldı.'
            })
        
        return data

    def save(self, **kwargs):
        """Email doğrulama işlemini gerçekleştirir."""
        user = self.context['request'].user
        code = self.validated_data['code']
        
        # Email'i doğrula
        success = user.profile.verify_email(code)
        
        if success:
            logger.info(f"Email verified for user: {user.username} (ID: {user.id})")
            return user
        else:
            raise serializers.ValidationError({
                'code': 'Doğrulama başarısız oldu.'
            })


class ResendVerificationSerializer(serializers.Serializer):
    """
    Doğrulama kodu yeniden gönderme için serializer.
    """
    
    def validate(self, data):
        """Yeniden gönderme koşullarını kontrol eder."""
        user = self.context['request'].user
        
        # UserProfile'ı kontrol et
        if not hasattr(user, 'profile'):
            raise serializers.ValidationError({
                'non_field_errors': ['Kullanıcı profili bulunamadı.']
            })
        
        profile = user.profile
        
        # Email zaten doğrulanmış mı?
        if profile.email_verified:
            raise serializers.ValidationError({
                'non_field_errors': ['Email adresi zaten doğrulanmış.']
            })
        
        # Cooldown kontrolü
        if not profile.can_request_new_code():
            raise serializers.ValidationError({
                'non_field_errors': ['Yeni kod isteyebilmek için 1 dakika beklemeniz gerekiyor.']
            })
        
        return data


class EmailVerificationStatusSerializer(serializers.Serializer):
    """
    Email doğrulama durumu için serializer.
    """
    email_verified = serializers.BooleanField(read_only=True)
    verification_code_expires = serializers.DateTimeField(read_only=True)
    verification_attempts = serializers.IntegerField(read_only=True)
    can_request_new_code = serializers.BooleanField(read_only=True)
    
    def to_representation(self, instance):
        """UserProfile instance'ından data çıkarır."""
        if hasattr(instance, 'profile'):
            profile = instance.profile
            return {
                'email_verified': profile.email_verified,
                'verification_code_expires': profile.verification_expires,
                'verification_attempts': profile.verification_attempts,
                'can_request_new_code': profile.can_request_new_code(),
            }
        else:
            return {
                'email_verified': False,
                'verification_code_expires': None,
                'verification_attempts': 0,
                'can_request_new_code': True,
            }