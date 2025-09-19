from django.db import models
from django.contrib.auth.models import User
import datetime
import json
import os
from io import BytesIO
from PIL import Image
from django.db import models
from django.core.files.base import ContentFile
from django.urls import reverse, NoReverseMatch





class VisitorSession(models.Model):
    session_key = models.CharField(max_length=100, unique=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_type = models.CharField(max_length=50, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    operating_system = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.session_key} - {self.start_time}"

class PageView(models.Model):
    url = models.CharField(max_length=500)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    referrer = models.CharField(max_length=500, blank=True, null=True)
    session_key = models.CharField(max_length=100)
    # Add foreign key relationship
    visitor_session = models.ForeignKey(
        VisitorSession, 
        on_delete=models.CASCADE, 
        related_name='page_views',
        null=True,  # Allow null for backward compatibility
        blank=True
    )
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.url} - {self.timestamp}"
    


# ============================
#  Helper function
# ============================
import datetime
from django.core.exceptions import ObjectDoesNotExist

def get_current_season():
    """Return the current active Season object, or the latest one as fallback."""
    today = datetime.date.today()

    season = Season.objects.filter(
        start_date__lte=today,
        end_date__gte=today
    ).first()

    if season:
        return season

    # fallback: latest season by start_date
    try:
        return Season.objects.latest("start_date")
    except ObjectDoesNotExist:
        return None  # if DB has no seasons at all



# ============================
#  Season Model
# ============================
class Season(models.Model):
    name = models.CharField(max_length=9, unique=True)  # e.g. "2025/2026"
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.name


# ============================
#  Club General Settings
# ============================
class ClubGeneralSettings(models.Model):
    club_name = models.CharField(max_length=255, default="Nugata FC")
    crest = models.ImageField(upload_to="team_logos/", null=True, blank=True)
    favicon = models.ImageField(upload_to="favicons/", null=True, blank=True)

    # Brand Colors
    primary_color = models.CharField(max_length=7, default="#228B22", blank=True)
    secondary_color = models.CharField(max_length=7, default="#FFD700", blank=True)
    neutral_dark = models.CharField(max_length=7, default="#000000", blank=True)
    neutral_light = models.CharField(max_length=7, default="#FFFFFF", blank=True)

    home_ground = models.CharField(max_length=255, blank=True)
    training_ground = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    site_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    google_analytics_id = models.CharField(max_length=50, blank=True)

    # 🔥 Default to current season
    current_season = models.ForeignKey(
        "Season",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="general_settings",
        default=get_current_season,
    )

    def save(self, *args, **kwargs):
        # Track the old season before saving
        old_season = None
        if self.pk:
            old_season = ClubGeneralSettings.objects.filter(pk=self.pk).values_list(
                "current_season", flat=True
            ).first()

        super().save(*args, **kwargs)

        # 🔥 If the current season changed → assign staff automatically
        if self.current_season and self.current_season.id != old_season:
            self.assign_staff_to_current_season()

        # Handle favicon resizing
        if self.favicon:
            sizes = [(16, 16), (32, 32), (180, 180), (192, 192), (512, 512)]
            base, ext = os.path.splitext(self.favicon.name)
            ext = ext.lower()
            for size in sizes:
                self._resize_favicon(size, base, ext)

    def assign_staff_to_current_season(self):
        """Assign eligible staff to the active season automatically."""
        from django.utils import timezone
        from dashboard.models import ClubTeamMember, StaffSeason

        season = self.current_season
        if not season:
            return

        today = timezone.now().date()

        eligible_staff = ClubTeamMember.objects.filter(
            date_joined__lte=season.end_date
        ).filter(
            models.Q(date_left__isnull=True) | models.Q(date_left__gte=season.start_date)
        )

        for staff in eligible_staff.distinct():
            StaffSeason.objects.get_or_create(staff=staff, season=season)

    def _resize_favicon(self, size, base, ext):
        """Helper to resize and save favicon in different sizes"""
        self.favicon.open()
        image = Image.open(self.favicon).convert("RGBA")
        image_resized = image.resize(size, Image.LANCZOS)
        buffer = BytesIO()
        image_resized.save(buffer, format="PNG")
        file_name = f"{base}_{size[0]}x{size[1]}.png"
        if self.favicon.storage.exists(file_name):
            self.favicon.storage.delete(file_name)
        self.favicon.storage.save(file_name, ContentFile(buffer.getvalue()))

    def get_menu_items(self):
        return [
            {"label": item.label, "url": item.get_url()}
            for item in self.menu_items.all()
        ]

    def add_menu_item(self, label, url_name=None, external_url=None, order=None):
        if order is None:
            max_order = self.menu_items.aggregate(models.Max("order"))[
                "order__max"
            ] or 0
            order = max_order + 1
        return MenuItem.objects.create(
            settings=self,
            label=label,
            url_name=url_name or "",
            external_url=external_url or "",
            order=order,
        )

    def __str__(self):
        return self.club_name or "Club Settings"


# ============================
#  Social Links
# ============================
class SocialLink(models.Model):
    PLATFORM_CHOICES = [
        ("facebook", "Facebook"),
        ("twitter", "Twitter / X"),
        ("instagram", "Instagram"),
        ("youtube", "YouTube"),
        ("tiktok", "TikTok"),
    ]

    club_settings = models.ForeignKey(
        ClubGeneralSettings,
        on_delete=models.CASCADE,
        related_name="social_links"
    )
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    url = models.URLField()

    class Meta:
        unique_together = ("club_settings", "platform")

    def __str__(self):
        return f"{self.get_platform_display()} - {self.url}"


# ============================
#  Menu Items
# ============================
class MenuItem(models.Model):
    settings = models.ForeignKey(
        ClubGeneralSettings,
        on_delete=models.CASCADE,
        related_name="menu_items"
    )
    label = models.CharField(max_length=100)
    url_name = models.CharField(max_length=100, blank=True, help_text="Django URL name")
    external_url = models.URLField(blank=True, help_text="Optional external link")
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first")

    class Meta:
        ordering = ['order']

    def get_url(self):
        if self.url_name:
            try:
                return reverse(self.url_name)
            except NoReverseMatch:
                return "#"
        return self.external_url or "#"

    def __str__(self):
        return self.label


# ============================
#  Staff Roles
# ============================
class ClubRole(models.Model):
    CATEGORY_CHOICES = [
        ("executive", "Executive"),
        ("technical", "Technical Staff"),
    ]

    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


# ============================
#  Team Members
# ============================
class ClubTeamMember(models.Model):
    picture = models.ImageField(upload_to="team_members/", null=True, blank=True)
    first_name = models.CharField(max_length=50, default="Blakk")
    last_name = models.CharField(max_length=50, default="Senses")
    date_of_birth = models.DateField(null=True, blank=True)
    role = models.ForeignKey(ClubRole, on_delete=models.SET_NULL, null=True, blank=True)
    date_joined = models.DateField()
    date_left = models.DateField(null=True, blank=True)

    user_account = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Link this team member to a CMS user (optional)."
    )

    # 🔥 Default to current season
    season = models.ForeignKey(
        Season,
        on_delete=models.CASCADE,
        related_name="club_members",
        default=get_current_season,
    )

    def is_active(self):
        return self.date_left is None

    def __str__(self):
        return f"{self.full_name} ({self.role.name if self.role else 'No Role'}) - {self.season}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


# ============================
#  Staff Season Assignments
# ============================
class StaffSeason(models.Model):
    staff = models.ForeignKey(ClubTeamMember, on_delete=models.CASCADE)
    season = models.ForeignKey(
        Season,
        on_delete=models.CASCADE,
        default=get_current_season,  # 🔥 Auto set to active season
    )

    class Meta:
        unique_together = ("staff", "season")

    def __str__(self):
        return f"{self.staff.full_name} - {self.season.name}"



class ClubIntegrationSettings(models.Model):
    mailchimp_api_key = models.CharField(max_length=255, blank=True, null=True)
    mailchimp_list_id = models.CharField(max_length=255, blank=True, null=True)
    whatsapp_group_link = models.URLField(blank=True, null=True)

    def __str__(self):
        return "Integration Settings"
