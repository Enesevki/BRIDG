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
    
    
class Report(models.Model):
    class ReportReasonChoices(models.TextChoices):
        BUG = 'BUG', 'Hata / Çalışmıyor'
        INAPPROPRIATE_CONTENT = 'INAPPROPRIATE', 'Uygunsuz İçerik'
        COPYRIGHT_INFRINGEMENT = 'COPYRIGHT', 'Telif Hakkı İhlali'
        SPAM_OR_MISLEADING = 'SPAM', 'Spam veya Yanıltıcı'
        OTHER = 'OTHER', 'Diğer'

    class ReportStatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Beklemede'
        REVIEWED = 'REVIEWED', 'İncelendi'
        RESOLVED = 'RESOLVED', 'Çözüldü'
        DISMISSED = 'DISMISSED', 'Reddedildi'

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,  # Raporlayan kullanıcı silinirse rapor kalsın, reporter null olsun
        null=True,  # Raporlayan kullanıcı null olabilir (isteğe bağlı, anonim raporlar için)
        blank=True,  # Formlarda boş bırakılabilir (isteğe bağlı)
        related_name='reports_made',
        help_text="Raporu gönderen kullanıcı (giriş yapmışsa)."
    )
    game = models.ForeignKey(
        'games.Game',
        on_delete=models.CASCADE,  # Oyun silinirse, raporları da silinsin
        related_name='reports_received',
        help_text="Raporlanan oyun."
    )
    reason = models.CharField(
        max_length=20,
        choices=ReportReasonChoices.choices,
        help_text="Raporun nedeni."
    )
    description = models.TextField(
        blank=True,  # Açıklama isteğe bağlı
        help_text="Rapor hakkında ek detaylar (isteğe bağlı)."
    )
    status = models.CharField(
        max_length=10,
        choices=ReportStatusChoices.choices,
        default=ReportStatusChoices.PENDING,
        help_text="Raporun mevcut durumu (admin tarafından yönetilir)."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Raporun oluşturulma zamanı."
    )
    # Admin tarafından güncellenecek alanlar
    updated_at = models.DateTimeField(
        auto_now=True,  # Rapor her güncellendiğinde (örneğin status değiştiğinde)
        help_text="Raporun son güncellenme zamanı."
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports_resolved',
        help_text="Raporu çözen veya inceleyen admin/yetkili kullanıcı."
    )

    class Meta:
        ordering = ['-created_at']  # En yeni raporlar önce
        verbose_name = "Report"
        verbose_name_plural = "Reports"
        # Bir kullanıcının aynı oyunu aynı nedenle tekrar tekrar raporlamasını engellemek için
        # unique_together = ('reporter', 'game', 'reason') # düşünülebilir, ama kullanıcı farklı
        # açıklamalarla aynı nedenle raporlamak isteyebilir. Bu kısıtlama şimdilik eklenmeyebilir.

    def __str__(self):
        return f"Report for '{self.game.title}' by {self.reporter.username if self.reporter else 'Anonymous'} - Reason: {self.get_reason_display()}"