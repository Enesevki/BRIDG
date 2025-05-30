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
    """Enhanced user serializer with input validation"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined']
        read_only_fields = ['id', 'date_joined']
    
    def validate_username(self, value):
        """Validate username with enhanced security"""
        try:
            return TextValidator.validate_username(value)
        except InputSecurityError as e:
            raise serializers.ValidationError(str(e))
    
    def validate_email(self, value):
        """Validate email with enhanced security"""
        try:
            return DataValidator.validate_email(value)
        except InputSecurityError as e:
            raise serializers.ValidationError(str(e))


class RegistrationSerializer(BaseValidationMixin, serializers.ModelSerializer):
    """Enhanced user registration serializer with comprehensive validation"""
    password2 = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2']
        extra_kwargs = {
            'password': {
                'write_only': True, 
                'min_length': 8,
                'style': {'input_type': 'password'},
                'help_text': 'Password must be at least 8 characters long.'
            },
            'email': {
                'required': True,
                'help_text': 'A valid email address is required.'
            },
            'username': {
                'help_text': 'Username can only contain letters, numbers, and underscores.'
            }
        }
    
    def get_validation_type(self):
        """Return validation type for BaseValidationMixin"""
        return 'user_registration'
    
    def validate_username(self, value):
        """Validate username with enhanced security"""
        try:
            validated_username = TextValidator.validate_username(value)
            
            # Check if username already exists (case-insensitive)
            if User.objects.filter(username__iexact=validated_username).exists():
                raise serializers.ValidationError("This username is already taken.")
            
            return validated_username
        except InputSecurityError as e:
            raise serializers.ValidationError(str(e))
    
    def validate_email(self, value):
        """Validate email with enhanced security"""
        try:
            validated_email = DataValidator.validate_email(value)
            
            # Check if email already exists
            if User.objects.filter(email__iexact=validated_email).exists():
                raise serializers.ValidationError("This email address is already registered.")
            
            return validated_email
        except InputSecurityError as e:
            raise serializers.ValidationError(str(e))
    
    def validate_password(self, value):
        """Enhanced password validation"""
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        
        # Check for common weak passwords
        common_passwords = ['password', '12345678', 'qwerty123', 'admin123']
        if value.lower() in common_passwords:
            raise serializers.ValidationError("This password is too common. Please choose a stronger password.")
        
        # Basic complexity check
        has_letter = any(c.isalpha() for c in value)
        has_digit = any(c.isdigit() for c in value)
        
        if not (has_letter and has_digit):
            raise serializers.ValidationError("Password must contain both letters and numbers.")
        
        return value
    
    def validate(self, data):
        """Enhanced full form validation"""
        try:
            # Apply comprehensive input validation first
            data = super().validate(data)
            
            # Password confirmation validation
            password = data.get('password')
            password2 = data.get('password2')
            
            if password != password2:
                raise serializers.ValidationError({
                    'password2': 'Password confirmation does not match.'
                })
            
            # Cross-field validation: username and email similarity
            username = data.get('username', '').lower()
            email = data.get('email', '').lower()
            
            if username and email:
                email_local = email.split('@')[0]  # Part before @
                if username == email_local:
                    raise serializers.ValidationError(
                        "Username cannot be the same as email address."
                    )
            
            return data
            
        except InputSecurityError as e:
            raise serializers.ValidationError(str(e))
    
    def create(self, validated_data):
        """Create user with enhanced security"""
        # Remove password2 from validated_data
        validated_data.pop('password2', None)
        
        # Create user with validated data
        user = User.objects.create_user(**validated_data)
        
        logger.info(f"New user registered: {user.username} (ID: {user.id})")
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


class PasswordChangeSerializer(serializers.Serializer):
    """Password change serializer with enhanced validation"""
    old_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    new_password2 = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    def validate_old_password(self, value):
        """Validate old password"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value
    
    def validate_new_password(self, value):
        """Enhanced new password validation"""
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        
        # Check for common weak passwords
        common_passwords = ['password', '12345678', 'qwerty123', 'admin123']
        if value.lower() in common_passwords:
            raise serializers.ValidationError("This password is too common. Please choose a stronger password.")
        
        # Basic complexity check
        has_letter = any(c.isalpha() for c in value)
        has_digit = any(c.isdigit() for c in value)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in value)
        
        if not (has_letter and has_digit):
            raise serializers.ValidationError("Password must contain both letters and numbers.")
        
        if len(value) >= 12 and not has_special:
            # For longer passwords, suggest special characters
            logger.info("User creating long password without special characters")
        
        return value
    
    def validate(self, data):
        """Validate password change form"""
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        new_password2 = data.get('new_password2')
        
        # Check password confirmation
        if new_password != new_password2:
            raise serializers.ValidationError({
                'new_password2': 'Password confirmation does not match.'
            })
        
        # Check that new password is different from old
        if old_password == new_password:
            raise serializers.ValidationError({
                'new_password': 'New password must be different from current password.'
            })
        
        return data
    
    def save(self):
        """Change user password"""
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        
        user.set_password(new_password)
        user.save()
        
        logger.info(f"Password changed for user: {user.username} (ID: {user.id})")
        return user