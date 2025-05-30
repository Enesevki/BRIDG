# backend/games/admin.py
from django.contrib import admin
from .models import Genre, Tag, Game


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'creator_username', 'is_published', 
        'moderation_status', 'moderation_status_display', 'created_at'
    )
    list_filter = ('is_published', 'moderation_status', 'genres', 'tags', 'creator')
    search_fields = ('title', 'description', 'creator__username')
    list_editable = ('is_published', 'moderation_status')
    
    readonly_fields = (
        'id', 'created_at', 'updated_at', 
        'likes_count', 'dislikes_count', 'play_count', 'view_count', 
        'entry_point_path', 'creator_link', 
        'thumbnail_display'  # <--- BU SATIRI EKLEYİN
    )
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'creator_link', 'thumbnail_display') # Artık readonly_fields'da olduğu için sorun çıkmaz
        }),
        ('Dosyalar ve Durum', {
            'fields': ('webgl_build_zip', 'thumbnail', 'entry_point_path', 'moderation_status', 'is_published') # 'thumbnail' alanı burada olmalı ki yüklenebilsin
        }),
        ('Kategorizasyon', {
            'fields': ('genres', 'tags')
        }),
        ('İstatistikler (Sadece Okunur)', {
            'fields': ('likes_count', 'dislikes_count', 'play_count', 'view_count'),
            'classes': ('collapse',)
        }),
        ('Zaman Damgaları (Sadece Okunur)', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    filter_horizontal = ('genres', 'tags',)

    def creator_username(self, obj):
        return obj.creator.username
    creator_username.short_description = 'Yükleyen'
    creator_username.admin_order_field = 'creator__username'

    def creator_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.creator:
            link = reverse("admin:auth_user_change", args=[obj.creator.id])
            return format_html('<a href="{}">{}</a>', link, obj.creator.username)
        return "-"
    creator_link.short_description = "Yükleyen Kullanıcı"

    def moderation_status_display(self, obj):
        return obj.get_moderation_status_display()
    moderation_status_display.short_description = 'Moderasyon Durumu (Okunabilir)'
    moderation_status_display.admin_order_field = 'moderation_status'

    def thumbnail_display(self, obj):
        from django.utils.html import format_html
        thumbnail_url = obj.get_thumbnail_url()
        if thumbnail_url:
            return format_html('<img src="{}" style="max-width: 200px; max-height: 200px;" />', thumbnail_url)
        return "Thumbnail Yok"
    thumbnail_display.short_description = "Mevcut Thumbnail"
    # thumbnail_display.allow_tags = True # Yeni Django versiyonlarında genellikle gereksiz

    # Eğer thumbnail_display'i fieldsets'in ilk bölümünde gösteriyorsak,
    # ve ayrıca thumbnail yükleme/değiştirme seçeneği de sunmak istiyorsak,
    # 'thumbnail' model alanını da 'Dosyalar ve Durum' fieldset'ine eklemeliyiz.
    # Yukarıdaki fieldsets tanımında bunu düzelttim.

























# We can customize the admin display later using ModelAdmin classes
# Example (We will uncomment and enhance this later):
# @admin.register(Game)
# class GameAdmin(admin.ModelAdmin):
#     list_display = ('title', 'creator', 'is_published', 'created_at')
#     list_filter = ('is_published', 'genres', 'tags', 'creator')
#     search_fields = ('title', 'description', 'creator__username')
#     readonly_fields = ('id', 'created_at', 'updated_at', 'likes_count', 'dislikes_count', 'play_count', 'view_count', 'entry_point_path')
#     fieldsets = (
#         (None, {
#             'fields': ('title', 'description', 'creator', 'thumbnail')
#         }),
#         ('Categorization', {
#             'fields': ('genres', 'tags')
#         }),
#          ('Files', {
#             'fields': ('webgl_build_zip',) # Entry point path is read-only
#         }),
#         ('Status & Timestamps', {
#             'fields': ('is_published', 'created_at', 'updated_at')
#         }),
#         ('Analytics (Read Only)', {
#             'fields': ('likes_count', 'dislikes_count', 'play_count', 'view_count'),
#             'classes': ('collapse',) # Make this section collapsible
#         }),
#     )
