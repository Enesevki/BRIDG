from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import random

# Email verification için User profile extension
class UserProfile(models.Model):
    """
    User model'ine ek olarak email verification bilgilerini tutar.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    email_verified = models.BooleanField(default=False, verbose_name='Email Doğrulandı')
    verification_code = models.CharField(max_length=6, null=True, blank=True, verbose_name='Doğrulama Kodu')
    verification_expires = models.DateTimeField(null=True, blank=True, verbose_name='Kod Geçerlilik Süresi')
    verification_attempts = models.IntegerField(default=0, verbose_name='Doğrulama Denemeleri')
    last_verification_request = models.DateTimeField(null=True, blank=True, verbose_name='Son Kod İsteği')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Kullanıcı Profili'
        verbose_name_plural = 'Kullanıcı Profilleri'
    
    def __str__(self):
        return f"{self.user.username} - Email Verified: {self.email_verified}"
    
    def generate_verification_code(self):
        """6 haneli doğrulama kodu oluşturur."""
        self.verification_code = f"{random.randint(100000, 999999)}"
        self.verification_expires = timezone.now() + timezone.timedelta(minutes=15)
        self.verification_attempts = 0
        self.last_verification_request = timezone.now()
        self.save()
        return self.verification_code
    
    def is_verification_code_valid(self, code):
        """Verilen kodun geçerli olup olmadığını kontrol eder."""
        if not self.verification_code or not self.verification_expires:
            return False
        
        # Kod süresi dolmuş mu?
        if timezone.now() > self.verification_expires:
            return False
        
        # Çok fazla deneme yapılmış mı?
        if self.verification_attempts >= 5:
            return False
        
        # Kod eşleşiyor mu?
        return self.verification_code == code
    
    def verify_email(self, code):
        """Email doğrulama işlemini gerçekleştirir."""
        if self.is_verification_code_valid(code):
            self.email_verified = True
            self.verification_code = None
            self.verification_expires = None
            self.verification_attempts = 0
            self.save()
            return True
        else:
            # Başarısız deneme sayısını artır
            self.verification_attempts += 1
            self.save()
            return False
    
    def can_request_new_code(self):
        """Yeni kod isteyip istemeyeceğini kontrol eder (1 dakika cooldown)."""
        if not self.last_verification_request:
            return True
        
        cooldown_time = timezone.now() - timezone.timedelta(minutes=1)
        return self.last_verification_request < cooldown_time


# Django signal ile otomatik UserProfile oluşturma
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """User oluşturulduğunda otomatik olarak UserProfile oluşturur."""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """User kaydedildiğinde profile'ı da kaydeder."""
    if hasattr(instance, 'profile'):
        instance.profile.save()
