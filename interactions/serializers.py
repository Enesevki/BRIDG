# backend/interactions/serializers.py

from rest_framework import serializers
from .models import Rating, Report
from users.serializers import UserSerializer  # UserSerializer'ı import et
# games.serializers içindeki GameSerializer'a veya UserSerializer'a gerek yok,
# çünkü genellikle rating işlemi yapılırken oyun veya kullanıcı ID'si alınır.
# Eğer yanıt olarak detaylı oyun/kullanıcı bilgisi dönmek isterseniz import edebilirsiniz.


class RatingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # User objesini UserSerializer ile göster
    # user_username alanına artık gerek yok, çünkü UserSerializer username'i zaten içerecek.

    class Meta:
        model = Rating
        fields = ['id', 'user', 'game', 'rating_type', 'created_at', 'updated_at']
        # read_only_fields'dan 'user' çıkarılabilir çünkü UserSerializer(read_only=True) zaten bunu sağlıyor.
        # Ancak view'da user hala request.user'dan atanacağı için,
        # bu alanın API'den POST/PUT ile gelmemesi için read_only kalması veya
        # fields listesinden çıkarılıp view'da atanması daha doğru olur.
        # En temizi, 'user'ı fields'da tutup read_only yapmak ve view'da atamak.
        read_only_fields = ['created_at', 'updated_at']  # 'user'ı view'da atayacağız.
                                                        # Dolayısıyla POST/PUT'ta beklenmeyecek.

        # Eğer user'ı POST/PUT'ta göndermek istemiyorsak (çünkü request.user'dan alıyoruz)
        # ve sadece yanıtta göstermek istiyorsak, UserSerializer(read_only=True) iyi bir yaklaşım.
        # Bu durumda, 'user' alanı fields'da kalmalı.

        # unique_together validasyonunu DRF'e bildirmek için (isteğe bağlı ama iyi pratik)
        # validators = [
        #     serializers.UniqueTogetherValidator(
        #         queryset=Rating.objects.all(),
        #         fields=['user', 'game'],
        #         message="Bu oyuna zaten oy verdiniz. Mevcut oyunuzu güncelleyebilirsiniz."
        #     )
        # ]
        # NOT: unique_together modelde tanımlı olduğu için DRF bunu genellikle
        # otomatik olarak anlar ve validasyon uygular. Ancak explicit olmak iyidir.
        # View seviyesinde get_or_create veya update_or_create kullanmak daha yaygındır.
    
    def validate_game(self, value):
        """
        Oyunun yayınlanmış olup olmadığını kontrol et (isteğe bağlı validasyon).
        Sadece yayınlanmış oyunlara oy verilebilsin.
        """
        # 'games.Game' modelini import etmeniz gerekir (dosyanın en başına)
        # from games.models import Game
        # if not value.is_published:
        #     raise serializers.ValidationError("Sadece yayınlanmış oyunlara oy verilebilir.")
        return value
    
    
class ReportSerializer(serializers.ModelSerializer):
    reporter_username = serializers.CharField(source='reporter.username', read_only=True, allow_null=True)
    # game_title'ı da read_only yapalım, çünkü game view'dan atanacak
    game_title = serializers.CharField(source='game.title', read_only=True, allow_null=True) # allow_null eklendi

    reason_display = serializers.CharField(source='get_reason_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    # Game alanını API yanıtında göstermek için, ancak POST/PUT'ta beklememek için
    # ya read_only=True yaparız ya da fields'dan çıkarıp view'da serialize ederken ekleriz.
    # Şimdilik read_only=True yapalım ve API yanıtında ID olarak görünsün.
    # Eğer detaylı game bilgisi isteniyorsa, GameSerializer ile iç içe kullanılabilir (read_only=True ile).
    game = serializers.PrimaryKeyRelatedField(read_only=True)  # <--- BU DEĞİŞİKLİK

    class Meta:
        model = Report
        fields = [
            'id', 'reporter', 'reporter_username',
            'game',  # Artık read_only, ID olarak dönecek
            'game_title',
            'reason', 'reason_display', 'description',
            'status', 'status_display', 'created_at', 'updated_at', 'resolved_by'
        ]
        read_only_fields = [
            'reporter', 'status', 'created_at', 'updated_at', 'resolved_by',
            'reporter_username', 'game_title', 'reason_display', 'status_display'
            # 'game' alanını yukarıda PrimaryKeyRelatedField(read_only=True) yaptık.
            # Bu yüzden artık buraya eklemeye gerek yok, ama zarar da vermez.
        ]

    def create(self, validated_data):
        """
        Rapor oluşturulurken reporter'ı isteği yapan kullanıcı olarak ayarlar.
        """
        # validated_data'da 'reporter' yok, çünkü read_only_fields'de.
        # 'reporter'ı context'ten veya view'dan almalıyız.
        # Şimdilik view'da perform_create içinde yapacağız.
        # report = Report.objects.create(**validated_data)
        # return report
        # VEYA serializer.save(reporter=request.user) view içinde çağrılacak.
        # Bu yüzden burada özel bir create'e gerek yok, ModelSerializer halleder.
        # Sadece 'reporter'ın view'dan geldiğinden emin olmalıyız.
        return super().create(validated_data)