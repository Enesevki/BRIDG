# backend/games/filters.py

import django_filters
from django.db import models
from .models import Game, Genre, Tag


class GameFilter(django_filters.FilterSet):
    """
    Django Filter for Game model to enable filtering by:
    - Genre (by ID or slug)
    - Tag (by ID or slug)
    - Search in title and description
    - Creator
    - Moderation status
    - Publication status
    """
    
    # Genre filtering - multiple genres can be selected
    genre = django_filters.ModelMultipleChoiceFilter(
        field_name='genres',
        queryset=Genre.objects.all(),
        conjoined=False,  # OR logic (game has ANY of the selected genres)
        # conjoined=True would be AND logic (game has ALL selected genres)
        error_messages={
            'invalid_choice': 'Invalid genre ID. Please provide valid genre IDs.',
            'invalid_list': 'Genre parameter must be a list of valid integers.'
        }
    )
    
    # Genre filtering by slug
    genre_slug = django_filters.ModelMultipleChoiceFilter(
        field_name='genres__slug',
        to_field_name='slug',
        queryset=Genre.objects.all(),
        conjoined=False,
        error_messages={
            'invalid_choice': 'Invalid genre slug. Please provide valid genre slugs.',
            'invalid_list': 'Genre slug parameter must be a list of valid strings.'
        }
    )
    
    # Tag filtering - multiple tags can be selected
    tag = django_filters.ModelMultipleChoiceFilter(
        field_name='tags',
        queryset=Tag.objects.all(),
        conjoined=False,  # OR logic (game has ANY of the selected tags)
        error_messages={
            'invalid_choice': 'Invalid tag ID. Please provide valid tag IDs.',
            'invalid_list': 'Tag parameter must be a list of valid integers.'
        }
    )
    
    # Tag filtering by slug
    tag_slug = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        conjoined=False,
        error_messages={
            'invalid_choice': 'Invalid tag slug. Please provide valid tag slugs.',
            'invalid_list': 'Tag slug parameter must be a list of valid strings.'
        }
    )
    
    # Search in title and description
    search = django_filters.CharFilter(
        method='filter_search',
        label='Search in title and description',
        help_text='Search for games by title or description'
    )
    
    # Creator filtering
    creator = django_filters.ModelChoiceFilter(
        field_name='creator',
        queryset=None,  # Will be set in __init__
        error_messages={
            'invalid_choice': 'Invalid creator ID. Please provide a valid user ID.'
        }
    )
    
    # Creator username filtering
    creator_username = django_filters.CharFilter(
        field_name='creator__username',
        lookup_expr='icontains',
        help_text='Filter by creator username (case insensitive)'
    )
    
    # Moderation status filtering
    moderation_status = django_filters.ChoiceFilter(
        field_name='moderation_status',
        choices=Game.ModerationStatusChoices.choices,
        error_messages={
            'invalid_choice': f'Invalid moderation status. Valid choices are: {[choice[0] for choice in Game.ModerationStatusChoices.choices]}'
        }
    )
    
    # Publication status
    is_published = django_filters.BooleanFilter(
        field_name='is_published',
        help_text='Filter by publication status (true/false)'
    )
    
    # Date range filtering
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        help_text='Show games created after this date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)'
    )
    
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        help_text='Show games created before this date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)'
    )
    
    # Ordering
    ordering = django_filters.OrderingFilter(
        fields=(
            ('created_at', 'created_at'),
            ('updated_at', 'updated_at'),
            ('title', 'title'),
            ('likes_count', 'likes_count'),
            ('dislikes_count', 'dislikes_count'),
            ('play_count', 'play_count'),
            ('view_count', 'view_count'),
        ),
        field_labels={
            'created_at': 'Creation Date',
            'updated_at': 'Update Date',
            'title': 'Title',
            'likes_count': 'Likes Count',
            'dislikes_count': 'Dislikes Count',
            'play_count': 'Play Count',
            'view_count': 'View Count',
        }
    )
    
    class Meta:
        model = Game
        fields = {
            # These are handled by custom filters above
            # 'genres': ['exact'],
            # 'tags': ['exact'],
            
            # Direct field filters
            'title': ['icontains'],
            'description': ['icontains'],
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set creator queryset dynamically
        from django.contrib.auth.models import User
        self.filters['creator'].queryset = User.objects.filter(uploaded_games__isnull=False).distinct()
    
    def filter_search(self, queryset, name, value):
        """
        Custom search filter that searches in both title and description
        """
        if not value:
            return queryset
        
        return queryset.filter(
            models.Q(title__icontains=value) |
            models.Q(description__icontains=value)
        ).distinct()


class PublishedGameFilter(GameFilter):
    """
    Filtered version of GameFilter that only shows published games.
    Useful for public API endpoints.
    """
    
    class Meta(GameFilter.Meta):
        # Inherit from parent but remove moderation_status and is_published
        # since we only want published games
        pass
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove filters that don't make sense for public API
        if 'moderation_status' in self.filters:
            del self.filters['moderation_status']
        if 'is_published' in self.filters:
            del self.filters['is_published'] 