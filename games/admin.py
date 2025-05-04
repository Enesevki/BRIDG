from django.contrib import admin
from .models import Genre, Tag, Game  # Import the models from the current app's models.py

# Simple registration (displays models with default settings)
admin.site.register(Genre)
admin.site.register(Tag)
admin.site.register(Game)


























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