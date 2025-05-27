from django.contrib import admin

# Register your models here.

# backend/interactions/admin.py
from django.contrib import admin
from .models import Rating  # Rating modelini import et

@admin.register(Rating)  # ModelAdmin ile özelleştirmek için @admin.register dekoratörünü kullanmak daha iyi bir yoldur
class RatingAdmin(admin.ModelAdmin):
    list_display = ('game', 'user', 'get_rating_type_display', 'created_at', 'updated_at')
    list_filter = ('rating_type', 'game', 'user') # Filtreleme seçenekleri
    search_fields = ('game__title', 'user__username') # Arama yapılacak alanlar
    readonly_fields = ('created_at', 'updated_at') # Sadece okunur alanlar

    # get_rating_type_display modelde tanımlı olduğu için list_display'de kullanılabilir.
    # Eğer modelde yoksa, burada bir metot tanımlayabilirdik:
    # def display_rating_type(self, obj):
    #     return obj.get_rating_type_display()
    # display_rating_type.short_description = 'Rating Type' # Kolon başlığı

# Veya en basit haliyle:
# admin.site.register(Rating)