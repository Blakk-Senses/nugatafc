from .models import ClubGeneralSettings

def club_settings(request):
    try:
        settings = ClubGeneralSettings.objects.first()
    except ClubGeneralSettings.DoesNotExist:
        settings = None

    return {
        "club_settings": settings,
        "brand_colors": {
            "primary": settings.primary_color if settings else "#228B22",
            "secondary": settings.secondary_color if settings else "#FFD700",
            "neutral_dark": settings.neutral_dark if settings else "#000000",
            "neutral_light": settings.neutral_light if settings else "#FFFFFF",
        },
    }


from .models import ClubTeamMember

def current_members(request):
    if request.user.is_authenticated:
        members = ClubTeamMember.objects.select_related("role", "user_account")
    else:
        members = []
    return {"members": members}
