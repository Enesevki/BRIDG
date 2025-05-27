from django.contrib import admin

# Register your models here.

# backend/interactions/admin.py
from django.contrib import admin
from .models import Rating, Report  # Rating modelini import et

@admin.register(Rating)  # ModelAdmin ile özelleştirmek için @admin.register dekoratörünü kullanmak daha iyi bir yoldur
class RatingAdmin(admin.ModelAdmin):
    list_display = ('game', 'user', 'get_rating_type_display', 'created_at', 'updated_at')
    list_filter = ('rating_type', 'game', 'user')  # Filtreleme seçenekleri
    search_fields = ('game__title', 'user__username')  # Arama yapılacak alanlar
    readonly_fields = ('created_at', 'updated_at')  # Sadece okunur alanlar

    # get_rating_type_display modelde tanımlı olduğu için list_display'de kullanılabilir.
    # Eğer modelde yoksa, burada bir metot tanımlayabilirdik:
    # def display_rating_type(self, obj):
    #     return obj.get_rating_type_display()
    # display_rating_type.short_description = 'Rating Type' # Kolon başlığı

# Veya en basit haliyle:
# admin.site.register(Rating)

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('game', 'reporter_display', 'get_reason_display', 'status', 'created_at') # 'reason_display' -> 'get_reason_display' olarak değiştirildi
    list_filter = ('status', 'reason', 'game', 'reporter')
    search_fields = ('game__title', 'reporter__username', 'description')
    list_editable = ('status',)
    # readonly_fields = ('created_at', 'updated_at', 'reporter', 'game', 'reason', 'description') # Bu satırda değişiklik yoktu, ama fieldsets'i kullanıyorsak,
                                                                                                 # bu satırı yorumlayabilir veya fieldsets ile uyumlu hale getirebiliriz.
                                                                                                 # Şimdilik fieldsets'e odaklanalım.

    fieldsets = (
        ("Rapor Bilgisi", {
            'fields': ('game_link', 'reporter_link', 'reason_display_form', 'description_display')
        }),
        ("Yönetim", {
            'fields': ('status', 'resolved_by')
        }),
        ("Zaman Damgaları", {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def reporter_display(self, obj):
        return obj.reporter.username if obj.reporter else "Anonim"
    reporter_display.short_description = "Raporlayan"
    reporter_display.admin_order_field = 'reporter__username' # Bu satırı ekleyerek bu kolona tıklanarak sıralama yapılmasını sağlayabiliriz.

    # Admin list_display için get_reason_display zaten modelde var.
    # Eğer özel bir gösterim isteseydik şöyle yapabilirdik:
    # def display_reason(self, obj):
    #     return obj.get_reason_display()
    # display_reason.short_description = "Rapor Nedeni"
    # display_reason.admin_order_field = 'reason' # Bu kolona tıklanarak sıralama yapılması için

    # Admin formunda okunabilir göstermek için fieldsets içinde kullandığımız metotlar
    def game_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.game:
            link = reverse("admin:games_game_change", args=[obj.game.id])
            return format_html('<a href="{}">{}</a>', link, obj.game.title)
        return "-"
    game_link.short_description = "Raporlanan Oyun"

    def reporter_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.reporter:
            link = reverse("admin:auth_user_change", args=[obj.reporter.id])
            return format_html('<a href="{}">{}</a>', link, obj.reporter.username)
        return "Anonim"
    reporter_link.short_description = "Raporlayan Kullanıcı"

    def reason_display_form(self, obj):  # Bu form için, list_display için değil
        return obj.get_reason_display()
    reason_display_form.short_description = "Rapor Nedeni"

    def description_display(self, obj):  # Bu form için
        return obj.description
    description_display.short_description = "Açıklama"

    def get_readonly_fields(self, request, obj=None):
        # Bu fieldsets ile yönetildiği için artık daha basit olabilir veya
        # fieldsets'deki 'fields' listesinde olmayan her şeyi readonly yapabiliriz.
        # Şimdilik fieldsets'in kendi mantığına güvenelim.
        # Eğer bir obje düzenleniyorsa, bazı alanları readonly yapmak isteyebiliriz.
        if obj:  # Obje düzenleniyorsa
            return ('created_at', 'updated_at', 'game_link', 'reporter_link', 'reason_display_form', 'description_display')
        return ('created_at', 'updated_at')  # Yeni obje oluşturuluyorsa (admin'den pek yapılmaz)

    # def has_add_permission(self, request):
    #     return False
    