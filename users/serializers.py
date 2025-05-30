# backend/users/serializers.py

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password  # Şifre politikalarını kontrol etmek için
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.tokens import RefreshToken


class RegistrationSerializer(serializers.ModelSerializer):
    """
    JWT token'ları ile birlikte kullanıcı kaydı için serializer.
    Kayıt sonrası otomatik olarak JWT token'ları döner.
    """
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="Bu e-posta adresi zaten kullanılıyor.")]
    )
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2')

    def validate(self, attrs):
        """
        Şifre doğrulaması ve diğer validasyonlar.
        """
        password = attrs.get('password')
        password2 = attrs.get('password2')

        if password != password2:
            raise serializers.ValidationError("Şifreler eşleşmiyor.")

        # Django'nun yerleşik şifre validasyonlarını çağıralım.
        # User instance'ını oluştururken 'password2'yi dışarıda bırakıyoruz.
        user_data_for_validation = {key: value for key, value in attrs.items() if key != 'password2'}
        temp_user = User(**user_data_for_validation)  # Geçici User objesi, sadece validasyon için

        try:
            validate_password(attrs['password'], user=temp_user)
        except serializers.ValidationError as e: # Django'nun ValidationError'ını DRF'inkine çeviriyoruz
            raise serializers.ValidationError({'password': list(e.messages)})
        except Exception as e: # Diğer olası Django validasyon hataları için
             # django.core.exceptions.ValidationError list of strings olarak değil,
             # direkt string olarak message dönebilir, bu yüzden e.messages yerine str(e)
             # kullanmak daha güvenli olabilir veya e.message_dict
            if hasattr(e, 'message_dict'):
                raise serializers.ValidationError(e.message_dict)
            elif hasattr(e, 'messages'):
                 raise serializers.ValidationError({'password': list(e.messages)})
            else:
                 raise serializers.ValidationError({'password': str(e)})

        return attrs

    def create(self, validated_data):
        """
        Kullanıcı oluştur ve JWT token'ları üret.
        """
        # password2'yi validated_data'dan çıkar çünkü User modeli bu alanı tanımıyor
        validated_data.pop('password2', None)

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        
        # JWT token'ları oluştur
        refresh = RefreshToken.for_user(user)
        
        # User instance'ına token'ları ekle (serializer'da kullanmak için)
        user.jwt_tokens = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Kullanıcı detayları için serializer.
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'date_joined')
        read_only_fields = ('id', 'date_joined')