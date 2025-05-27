# backend/interactions/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Rating
from games.models import Game  # Game modelini import et
from django.db.models import Count, Q


@receiver(post_save, sender=Rating)
def update_game_rating_counts_on_save(sender, instance, created, **kwargs):
    """
    Bir Rating objesi kaydedildiğinde (oluşturulduğunda veya güncellendiğinde)
    ilgili Game modelinin likes_count ve dislikes_count alanlarını günceller.
    """
    game = instance.game
    # O game için tüm Like'ları say
    game.likes_count = Rating.objects.filter(game=game, rating_type=Rating.RatingChoices.LIKE).count()
    # O game için tüm Dislike'ları say
    game.dislikes_count = Rating.objects.filter(game=game, rating_type=Rating.RatingChoices.DISLIKE).count()
    game.save(update_fields=['likes_count', 'dislikes_count'])  # Sadece bu alanları güncelle


@receiver(post_delete, sender=Rating)
def update_game_rating_counts_on_delete(sender, instance, **kwargs):
    """
    Bir Rating objesi silindiğinde ilgili Game modelinin
    likes_count ve dislikes_count alanlarını günceller.
    """
    # update_game_rating_counts_on_save ile aynı mantık, çünkü silindikten sonra tekrar sayım yapıyoruz.
    # instance.game hala erişilebilir durumda olmalı (ilişki silinmeden önce).
    game = instance.game
    if game:  # Oyun hala varsa (nadiren de olsa oyun da aynı anda silinmiş olabilir)
        game.likes_count = Rating.objects.filter(game=game, rating_type=Rating.RatingChoices.LIKE).count()
        game.dislikes_count = Rating.objects.filter(game=game, rating_type=Rating.RatingChoices.DISLIKE).count()
        game.save(update_fields=['likes_count', 'dislikes_count'])
