from django.db import models

# Create your models here.

from django.db import models
from django.conf import settings  # User modeline referans için
# from games.models import Game # Direkt import yerine string referans daha iyi olabilir
                                # ama aynı proje içinde genellikle sorun olmaz.
                                # String referans: 'games.Game'


class Rating(models.Model):
    class RatingChoices(models.IntegerChoices):
        # Değerler: Veritabanında saklanacak değer, Etiket: API'de/Admin'de görünecek okunabilir isim
        LIKE = 1, 'Like'
        DISLIKE = -1, 'Dislike'
        # İleride nötr veya farklı oylama türleri eklenebilir
        # NEUTRAL = 0, 'Neutral'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Django'nun aktif User modeline referans
        on_delete=models.CASCADE,  # Kullanıcı silinirse, oyları da silinsin
        related_name='ratings_given',  # User.ratings_given.all() ile kullanıcının verdiği oylara erişim
        help_text="Oyu veren kullanıcı."
    )
    game = models.ForeignKey(
        'games.Game',  # Game modeline string referans (dairesel importları önler)
        on_delete=models.CASCADE,  # Oyun silinirse, oyları da silinsin
        related_name='ratings',   # Game.ratings.all() ile oyunun aldığı oylara erişim
        help_text="Oylanan oyun."
    )
    rating_type = models.IntegerField(
        choices=RatingChoices.choices,
        help_text="Kullanıcının verdiği oy (Like/Dislike)."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Oyun oluşturulma zamanı."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Oyun son güncellenme zamanı."
    )  # Kullanıcı oyunu değiştirirse bu güncellenir

    class Meta:
        # Bir kullanıcının bir oyuna sadece bir kez oy verebilmesini sağlar.
        unique_together = ('user', 'game')
        ordering = ['-created_at']  # En yeni oylar önce
        verbose_name = "Rating"
        verbose_name_plural = "Ratings"

    def __str__(self):
        return f"{self.user.username} rated {self.game.title} as {self.get_rating_type_display()}"