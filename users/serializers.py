# backend/users/serializers.py

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password # Şifre politikalarını kontrol etmek için
from rest_framework import serializers
from rest_framework.validators import UniqueValidator


class RegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="Bu e-posta adresi zaten kullanılıyor.")]
    )
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True, label="Şifre (Tekrar)")

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2')
        extra_kwargs = {
            'password': {'write_only': True, 'style': {'input_type': 'password'}, 'label': "Şifre"}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Şifreler eşleşmiyor."})

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
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user
    

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')