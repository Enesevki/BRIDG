from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class EmailVerificationService:
    """
    Email doğrulama servisi - BRIDG branding ile
    """
    
    EMAIL_SUBJECT = "BRIDG'e hoş geldin! Hadi hesabını doğrulayalım 🎮"
    FROM_EMAIL = "BRIDG Ekibi <noreply@bridg-platform.com>"
    
    @staticmethod
    def send_verification_email(user, code):
        """
        Kullanıcıya email doğrulama kodu gönderir.
        
        Args:
            user: Django User instance
            code: 6 haneli doğrulama kodu
            
        Returns:
            bool: Email gönderim başarı durumu
        """
        try:
            subject = EmailVerificationService.EMAIL_SUBJECT
            from_email = EmailVerificationService.FROM_EMAIL
            to_email = [user.email]
            
            # Email context data
            context = {
                'username': user.username,
                'verification_code': code,
                'user_email': user.email
            }
            
            # HTML template render (template'i oluşturacağız)
            try:
                html_content = render_to_string('emails/verification_email.html', context)
            except Exception as template_error:
                logger.warning(f"HTML template error, using plain text: {template_error}")
                html_content = None
            
            # Plain text fallback - her zaman çalışır
            text_content = f"""
Merhaba {user.username},

BRIDG'e katıldığın için çok mutluyuz! 🧡

Topluluğumuza adım atmadan önce, sadece bir adım kaldı:
Aşağıdaki doğrulama kodunu kullanarak e-posta adresini onayla:

{code}

Bu kod 15 dakika boyunca geçerlidir, sonrasında sihrini kaybeder! ⏳
Sorun yaşarsan bizimle iletişime geçmekten çekinme.

Keyifli oyunlar!
— BRIDG Ekibi

Bu e-posta otomatik olarak gönderilmiştir. Lütfen yanıtlamayın.
            """
            
            # Email mesajını oluştur
            msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
            
            # HTML alternatifi varsa ekle
            if html_content:
                msg.attach_alternative(html_content, "text/html")
            
            # Email gönder
            msg.send()
            
            logger.info(f"Verification email sent to {user.email} (User: {user.username})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_welcome_email(user):
        """
        Email doğrulama sonrası hoş geldin email'i gönderir.
        
        Args:
            user: Django User instance
            
        Returns:
            bool: Email gönderim başarı durumu
        """
        try:
            subject = "🎉 BRIDG'e hoş geldin! Hesabın hazır!"
            from_email = EmailVerificationService.FROM_EMAIL
            to_email = [user.email]
            
            text_content = f"""
Tebrikler {user.username}!

Email adresin başarıyla doğrulandı ve BRIDG topluluğuna katıldın! 🎉

Artık şunları yapabilirsin:
• WebGL oyunlarını keşfet ve oyna
• Kendi oyunlarını yükle ve paylaş  
• Oyunları beğen ve değerlendir
• Toplulukla etkileşime geç

Hadi, ilk oyununu keşfetmeye başla!

BRIDG'e hoş geldin! 🧡
— BRIDG Ekibi
            """
            
            msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
            msg.send()
            
            logger.info(f"Welcome email sent to {user.email} (User: {user.username})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def is_email_configured():
        """
        Email yapılandırmasının doğru olup olmadığını kontrol eder.
        
        Returns:
            bool: Email config durumu
        """
        required_settings = [
            'EMAIL_HOST',
            'EMAIL_PORT', 
            'EMAIL_HOST_USER',
            'EMAIL_HOST_PASSWORD'
        ]
        
        for setting in required_settings:
            if not hasattr(settings, setting) or not getattr(settings, setting):
                logger.warning(f"Email configuration missing: {setting}")
                return False
        
        return True 