from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.utils import timezone
from .models import UserProfile


# ============================================================================
# CUSTOM USER ADMIN
# ============================================================================

class CustomUserAdmin(BaseUserAdmin):
    """Enhanced User admin with email verification status."""
    
    list_display = (
        'username', 
        'email', 
        'first_name', 
        'last_name',
        'email_verification_status',
        'is_staff', 
        'date_joined'
    )
    
    list_filter = (
        'is_staff', 
        'is_superuser',
        'profile__email_verified',  # Email verification filter
        'date_joined'
    )
    
    search_fields = ('username', 'first_name', 'last_name', 'email')
    
    # Add email verification status column
    def email_verification_status(self, obj):
        """Show email verification status with color coding."""
        if hasattr(obj, 'profile'):
            if obj.profile.email_verified:
                return format_html(
                    '<span style="background: #d4edda; color: #155724; padding: 2px 6px; border-radius: 3px;">✅ Doğrulandı</span>'
                )
            else:
                return format_html(
                    '<span style="background: #f8d7da; color: #721c24; padding: 2px 6px; border-radius: 3px;">❌ Doğrulanmadı</span>'
                )
        else:
            return format_html(
                '<span style="background: #e2e3e5; color: #6c757d; padding: 2px 6px; border-radius: 3px;">❓ Profil Yok</span>'
            )
    email_verification_status.short_description = 'Email Doğrulama'
    email_verification_status.admin_order_field = 'profile__email_verified'


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# ============================================================================
# USERPROFILE ADMIN
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
