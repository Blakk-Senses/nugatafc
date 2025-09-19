from django.db.models.signals import post_save
from django.dispatch import receiver
from matches.models import Team
import os
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import ClubTeamMember, StaffSeason, ClubGeneralSettings



@receiver(post_save, sender=ClubGeneralSettings)
def ensure_club_team_exists(sender, instance, **kwargs):
    if instance.club_name:
        team, created = Team.objects.get_or_create(
            name=instance.club_name,
            defaults={
                "stadium": instance.home_ground,
                "logo": instance.crest
            }
        )
        # optional: update existing team if details changed
        if not created:
            team.stadium = instance.home_ground
            if instance.crest:
                team.logo = instance.crest
            team.save()




@receiver(pre_save, sender=ClubGeneralSettings)
def delete_old_favicon(sender, instance, **kwargs):
    """Delete old favicon + resized versions when a new one is uploaded"""
    if not instance.pk:
        return  # new object, nothing to delete

    try:
        old = ClubGeneralSettings.objects.get(pk=instance.pk)
    except ClubGeneralSettings.DoesNotExist:
        return

    old_favicon = old.favicon
    new_favicon = instance.favicon

    if old_favicon and old_favicon != new_favicon:
        base, ext = os.path.splitext(old_favicon.name)
        sizes = [(16, 16), (32, 32), (180, 180), (192, 192), (512, 512)]

        # Delete original
        if old_favicon.storage.exists(old_favicon.name):
            old_favicon.storage.delete(old_favicon.name)

        # Delete resized
        for size in sizes:
            file_name = f"{base}_{size[0]}x{size[1]}.png"
            if old_favicon.storage.exists(file_name):
                old_favicon.storage.delete(file_name)




@receiver(post_save, sender=ClubTeamMember)
def create_staff_season(sender, instance, created, **kwargs):
    if created:
        # Get current season from CMS settings
        settings = ClubGeneralSettings.objects.first()
        if settings and settings.current_season:
            StaffSeason.objects.get_or_create(
                staff=instance,
                season=settings.current_season
            )
