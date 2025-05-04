from django.db import models
import uuid  # Required for generating UUIDs for Game IDs
from django.db import models
from django.contrib.auth.models import User # Django's built-in User model
from django.core.validators import FileExtensionValidator # To validate uploaded file types
from django.utils.text import slugify # To help generate slugs automatically


# Create your models here.

class Genre(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="The name of the genre (e.g., Action, Puzzle, Strategy)."
    )
    slug = models.SlugField(
        max_length=110, # Slightly larger than name to accommodate potential additions
        unique=True,
        blank=True, # Allow blank in the form, we'll auto-populate it
        help_text="URL-friendly identifier for the genre. Auto-generated if left blank."
    )

    class Meta:
        ordering = ['name'] # Order genres alphabetically by default

    def save(self, *args, **kwargs):
        # Auto-generate slug from name if it's blank
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs) # Call the "real" save() method.

    def __str__(self):
        """String for representing the Model object (e.g., in Admin site)."""
        return self.name
    
    
class Tag(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="The name of the tag (e.g., Multiplayer, Physics, 2D)."
    )
    slug = models.SlugField(
        max_length=110,
        unique=True,
        blank=True,
        help_text="URL-friendly identifier for the tag. Auto-generated if left blank."
    )

    class Meta:
        ordering = ['name'] # Order tags alphabetically by default

    def save(self, *args, **kwargs):
        # Auto-generate slug from name if it's blank
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        """String for representing the Model object."""
        return self.name
    
    
class Game(models.Model):
    # Core Fields
    id = models.UUIDField(
        primary_key=True,      # Make this the primary key instead of default integer ID
        default=uuid.uuid4,    # Generate a UUID automatically on creation
        editable=False,        # Prevent editing the ID after creation
        help_text="Unique identifier for the game (UUID)."
    )
    title = models.CharField(
        max_length=200,
        help_text="The title of the game."
    )
    description = models.TextField(
        blank=True, # Allow description to be optional
        help_text="A detailed description of the game."
    )

    # Relationships
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,  # If the user is deleted, delete their games too
        related_name='uploaded_games',  # How to access games from the User model (user.uploaded_games.all())
        help_text="The user who uploaded this game."
    )
    genres = models.ManyToManyField(
        Genre,
        blank=True,  # Allow games to have no genres initially
        related_name='games',  # How to access games from the Genre model (genre.games.all())
        help_text="Select genres for this game."
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,  # Allow games to have no tags initially
        related_name='games',  # How to access games from the Tag model (tag.games.all())
        help_text="Select tags for this game."
    )

    # File Fields (Path stored in DB, actual file usually in cloud storage/media dir)
    webgl_build_zip = models.FileField(
        upload_to='game_builds/zips/',  # Store original zips in MEDIA_ROOT/game_builds/zips/
        validators=[FileExtensionValidator(allowed_extensions=['zip'])],
        help_text="Upload a ZIP file containing the Unity WebGL build (Build/, TemplateData/, index.html)."
    )
    # Store the relative path to the main index.html file AFTER extraction
    # This will be set programmatically during the upload process, not directly by the user
    entry_point_path = models.CharField(
        max_length=255,
        blank=True,      # Can be blank until processed
        null=True,       # Can be null in the database until processed
        editable=False,  # Not directly editable in admin forms
        help_text="Relative path to the game's entry point (e.g., index.html) after extraction."
    )
    thumbnail = models.ImageField(
        upload_to='game_thumbnails/',  # Store thumbnails in MEDIA_ROOT/game_thumbnails/
        blank=True,                 # Thumbnail is optional
        null=True,                  # Allow null in the database
        help_text="Upload a thumbnail image for the game."
    )

    # Status & Timestamps
    is_published = models.BooleanField(
        default=False,  # Games must be explicitly published (e.g., by an admin)
        help_text="Is the game visible to the public?"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,  # Automatically set timestamp when the game object is first created
        help_text="Timestamp when the game was first added."
    )
    updated_at = models.DateTimeField(
        auto_now=True,     # Automatically update timestamp every time the game object is saved
        help_text="Timestamp when the game was last updated."
    )

    # Aggregated data / Analytics (updated via signals or tasks later)
    # Using PositiveIntegerField ensures these counts can't be negative.
    likes_count = models.PositiveIntegerField(
        default=0,
        editable=False,  # Should be calculated, not edited directly
        help_text="Number of likes the game has received."
    )
    dislikes_count = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text="Number of dislikes the game has received."
    )
    play_count = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text="Number of times the game has been played (approximate)."
    )
    view_count = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text="Number of times the game detail page has been viewed."
    )

    class Meta:
        ordering = ['-created_at'] # Show newest games first by default

    def __str__(self):
        """String for representing the Model object."""
        return f"{self.title} (by {self.creator.username})"
