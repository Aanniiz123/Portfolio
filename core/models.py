from django.db import models


class VideoProject(models.Model):
    """A video editing project shown on the home page."""

    CATEGORY_CHOICES = [
        ("music",      "Music Video"),
        ("visualizer", "Visualizer"),
        ("cinematic",  "Cinematic Edit"),
        ("promo",      "Artist Promo"),
        ("lyric",      "Lyric / Typography"),
        ("atmospheric","Atmospheric / Experimental"),
        ("social",     "Social Content"),
        ("spiritual",  "Artistic / Spiritual"),
        ("other",      "Other"),
    ]

    title = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    category = models.CharField(
        max_length=60,
        choices=CATEGORY_CHOICES,
        default="other",
    )
    client = models.CharField(max_length=160, blank=True)
    description = models.TextField(blank=True)
    video_url = models.URLField(
        help_text="YouTube/Vimeo direct link or .mp4 URL.",
    )
    thumbnail = models.ImageField(upload_to="thumbnails/", blank=True)
    cover_color = models.CharField(
        max_length=7,
        default="#a855f7",
        help_text="Hex fallback colour behind the thumbnail.",
    )
    featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "-created_at"]
        indexes = [models.Index(fields=["featured", "order"])]

    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    """Stores inbound contact form submissions for the admin."""

    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=150)
    message = models.TextField()
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-received_at"]

    def __str__(self):
        return f"{self.subject} — {self.name}"