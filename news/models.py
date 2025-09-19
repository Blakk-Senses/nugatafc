from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from taggit.managers import TaggableManager
from django.utils.text import Truncator
from PIL import Image
import os
from django.conf import settings




class News(models.Model):
    CATEGORY_CHOICES = [
        ("training", "Training"),
        ("transfer", "Transfer"),
        ("report", "Match Report"),
        ("general", "News"),
    ]
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
    ]

    # Core
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    excerpt = models.TextField(blank=True)
    content = CKEditor5Field("Content", config_name="default")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="general")
    cover_image = models.ImageField(upload_to="news/", blank=True, null=True)
    thumbnail = models.ImageField(upload_to="news/thumbnails/", blank=True, null=True)

    # ✅ SEO fields
    seo_title = models.CharField(max_length=255, blank=True)
    seo_description = models.TextField(blank=True)
    seo_keywords = models.CharField(max_length=255, blank=True)

    # ✅ Social fields
    og_image = models.ImageField(upload_to="news/social/", blank=True, null=True)

    # ✅ Settings fields
    allow_comments = models.BooleanField(default=True)

    # Metadata
    date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")
    author = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    tags = TaggableManager(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # --- AUTO SEO FALLBACKS ---
        if not self.seo_title:
            self.seo_title = self.title

        if not self.seo_description:
            if self.excerpt:
                self.seo_description = Truncator(self.excerpt).chars(160)
            elif self.content:
                self.seo_description = Truncator(self.content).chars(160)

        if not self.seo_keywords and self.pk:  # requires instance to exist
            self.seo_keywords = ", ".join(self.tags.values_list("name", flat=True))

        # --- AUTO SOCIAL FALLBACK ---
        if not self.og_image and self.cover_image:
            self.og_image = self.cover_image

        # --- CALL ORIGINAL SAVE ---
        super().save(*args, **kwargs)

        # --- THUMBNAIL GENERATION ---
        if self.cover_image:
            cover_path = os.path.join(settings.MEDIA_ROOT, self.cover_image.name)

            if os.path.exists(cover_path):  # avoid errors if file missing
                img = Image.open(cover_path)
                img.thumbnail((400, 250))  # width x height
                thumb_name = f"thumb_{os.path.basename(self.cover_image.name)}"
                thumb_path = os.path.join(settings.MEDIA_ROOT, "news/thumbnails", thumb_name)

                os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
                img.save(thumb_path, format="JPEG", quality=80)

                # Save path in model
                if not self.thumbnail or self.thumbnail.name != f"news/thumbnails/{thumb_name}":
                    self.thumbnail = f"news/thumbnails/{thumb_name}"
                    super().save(update_fields=["thumbnail"])

    def get_meta_title(self):
        return self.seo_title or self.title

    def get_meta_description(self):
        return self.seo_description or self.excerpt or Truncator(self.content).chars(160)

    def __str__(self):
        return self.title
