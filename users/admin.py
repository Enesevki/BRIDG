from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import UserProfile


# ============================================================================
# USERPROFILE ADMIN ONLY
# ============================================================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """UserProfile için admin interface."""
    
    list_display = (
        'user_info',
        'email_verified_status', 
        'verification_code_status',
        'verification_attempts',
        'last_verification_request',
        'created_at'
    )
    
    list_filter = (
        'email_verified',
        'created_at',
        'updated_at'
    )
    
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    
    readonly_fields = ('created_at', 'updated_at')
    
    # Özel sütun görünümleri
    def user_info(self, obj):
        """Kullanıcı bilgilerini gösterir."""
        return format_html(
            '<strong>{}</strong><br/><small>{}</small>',
            obj.user.username,
            obj.user.email
        )
    user_info.short_description = 'Kullanıcı'
    
    def email_verified_status(self, obj):
        """Email doğrulama durumunu renkli gösterir."""
        if obj.email_verified:
            return format_html(
                '<span style="background: #d4edda; color: #155724; padding: 2px 6px; border-radius: 3px;">✅ Doğrulandı</span>'
            )
        else:
            return format_html(
                '<span style="background: #f8d7da; color: #721c24; padding: 2px 6px; border-radius: 3px;">❌ Bekliyor</span>'
            )
    email_verified_status.short_description = 'Email Durumu'
    
    def verification_code_status(self, obj):
        """Doğrulama kodu durumunu gösterir."""
        if not obj.verification_code:
            return format_html('<span style="color: gray;">-</span>')
        
        if obj.verification_expires and timezone.now() > obj.verification_expires:
            return format_html(
                '<span style="color: red;">⏰ Süresi Dolmuş</span>'
            )
        elif obj.verification_code:
            return format_html(
                '<span style="color: orange;">🔑 Aktif Kod</span>'
            )
    verification_code_status.short_description = 'Kod Durumu'


# ============================================================================
# ADMIN SITE BRANDING
# ============================================================================

admin.site.site_header = "🎮 BRIDG Admin Panel"
admin.site.site_title = "BRIDG Admin"
admin.site.index_title = "BRIDG Platform Yönetimi"
