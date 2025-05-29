from django.db import models
import uuid  # Required for generating UUIDs for Game IDs
from django.db import models
from django.contrib.auth.models import User  # Django's built-in User model
from django.core.validators import (
    FileExtensionValidator,
)  # To validate uploaded file types
from django.utils.text import slugify  # To help generate slugs automatically


# Create your models here.


class Genre(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="The name of the genre (e.g., Action, Puzzle, Strategy).",
    )
    slug = models.SlugField(
        max_length=110,  # Slightly larger than name to accommodate potential additions
        unique=True,
        blank=True,  # Allow blank in the form, we'll auto-populate it
        help_text="URL-friendly identifier for the genre. Auto-generated if left blank.",
    )

    class Meta:
        ordering = ["name"]  # Order genres alphabetically by default

    def save(self, *args, **kwargs):
        # Auto-generate slug from name if it's blank
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)  # Call the "real" save() method.

    def __str__(self):
        """String for representing the Model object (e.g., in Admin site)."""
        return self.name


class Tag(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="The name of the tag (e.g., Multiplayer, Physics, 2D).",
    )
    slug = models.SlugField(
        max_length=110,
        unique=True,
        blank=True,
        help_text="URL-friendly identifier for the tag. Auto-generated if left blank.",
    )

    class Meta:
        ordering = ["name"]  # Order tags alphabetically by default

    def save(self, *args, **kwargs):
        # Auto-generate slug from name if it's blank
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        """String for representing the Model object."""
        return self.name


class Game(models.Model):
    class ModerationStatusChoices(models.TextChoices):
        PENDING_CHECKS = "PENDING_CHECKS", "Waiting for automatic checks"
        CHECKS_PASSED = "CHECKS_PASSED", "Automatic checks passed"
        CHECKS_FAILED = "CHECKS_FAILED", "Automatic checks failed"
        PENDING_REVIEW = (
            "PENDING_REVIEW",
            "Waiting for manual review",
        )  # After CHECKS_PASSED, it may transition here
        
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the game, generated automatically.",
    )
    title = models.CharField(
        max_length=200,
        help_text="The title of the game, displayed to users.",
    )
    description = models.TextField(
        blank=True,
        help_text="A brief description of the game, providing details about gameplay or features.",
    )
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="uploaded_games",
        help_text="The user who uploaded or created the game.",
    )
    genres = models.ManyToManyField(
        Genre,
        blank=True,
        related_name="games",
        help_text="Genres associated with the game, such as Action or Puzzle.",
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="games",
        help_text="Tags describing the game, such as Multiplayer or Physics.",
    )
    webgl_build_zip = models.FileField(
        upload_to="game_builds/zips/",
        validators=[FileExtensionValidator(allowed_extensions=["zip"])],
        help_text="The ZIP file containing the WebGL build of the game.",
    )
    entry_point_path = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        editable=False,
        help_text="Path to the entry point file within the WebGL build ZIP.",
    )
    thumbnail = models.ImageField(
        upload_to="game_thumbnails/",
        blank=True,
        null=True,
        help_text="Thumbnail image representing the game.",
    )

    # Moderation and Publication Status
    moderation_status = models.CharField(
        max_length=20,
        choices=ModerationStatusChoices.choices,
        default=ModerationStatusChoices.PENDING_CHECKS,
        help_text="The moderation status of the game, indicating its review progress.",
    )
    is_published = models.BooleanField(
        default=False,
        help_text="Indicates whether the game is publicly visible after admin approval.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time when the game was created.",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="The date and time when the game was last updated.",
    )
    likes_count = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text="The number of likes the game has received.",
    )
    dislikes_count = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text="The number of dislikes the game has received.",
    )
    play_count = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text="The number of times the game has been played.",
    )
    view_count = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text="The number of times the game has been viewed.",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} (by {self.creator.username})"
