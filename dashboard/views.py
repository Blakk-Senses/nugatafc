from django.shortcuts import render, redirect, get_object_or_404
from news.models import News
from matches.models import Standing
from news.forms import (
    NewsCoreForm, NewsSEOForm, NewsSettingsForm, NewsSocialForm
)
from matches.forms import StandingForm 
from dashboard.models import (
    ClubGeneralSettings, ClubIntegrationSettings, MenuItem,
    ClubTeamMember, ClubRole, SocialLink, Season, get_current_season
)
from dashboard.forms import (
    ClubGeneralSettingsForm, ClubIntegrationSettingsForm,
    ClubRoleForm, ClubTeamMemberForm, AssignCMSUserForm, 
    SocialLinkForm, MenuItemForm
)
from players.models import Player
from players.forms import PlayerForm
from django.contrib.auth.decorators import login_required
from datetime import date
from django.utils import timezone
from django.db.models import Q, Count, Avg, ExpressionWrapper, DurationField, F
from django.db.models.functions import TruncDate
from datetime import timedelta
from .models import PageView, VisitorSession
from django.contrib import messages
from django.urls import reverse
from django.forms import inlineformset_factory




@login_required
def news_manager(request):
    news = News.objects.all()

    # Search
    query = request.GET.get("q")
    if query:
        news = news.filter(
            Q(title__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(content__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()

    # Filter by status
    status = request.GET.get("status")
    if status:
        news = news.filter(status=status)

    # Filter by category
    category = request.GET.get("category")
    if category:
        news = news.filter(category=category)

    # Sorting
    sort = request.GET.get("sort", "-created_at")
    news = news.order_by(sort)

    return render(request, "dashboard/news_manager.html", {"news": news})


@login_required
def news_create(request):
    if request.method == "POST":
        core_form = NewsCoreForm(request.POST, request.FILES, prefix="core")
        seo_form = NewsSEOForm(request.POST, prefix="seo")
        social_form = NewsSocialForm(request.POST, request.FILES, prefix="social")
        settings_form = NewsSettingsForm(request.POST, prefix="settings")

        forms = [core_form, seo_form, social_form, settings_form]

        if all(f.is_valid() for f in forms):
            news = core_form.save(commit=False)
            news.author = request.user
            news.status = "published" if "publish" in request.POST else "draft"
            news.save()

            core_form.save_m2m()  # this now takes care of tags

            seo_form = NewsSEOForm(request.POST, instance=news, prefix="seo")
            social_form = NewsSocialForm(request.POST, request.FILES, instance=news, prefix="social")
            settings_form = NewsSettingsForm(request.POST, instance=news, prefix="settings")

            seo_form.save()
            social_form.save()
            settings_form.save()

            return redirect("dashboard:news_manager")
    else:
        core_form = NewsCoreForm(prefix="core")
        seo_form = NewsSEOForm(prefix="seo")
        social_form = NewsSocialForm(prefix="social")
        settings_form = NewsSettingsForm(prefix="settings")

    return render(request, "dashboard/news_form.html", {
        "core_form": core_form,
        "seo_form": seo_form,
        "social_form": social_form,
        "settings_form": settings_form,
        "all_forms": [core_form, seo_form, social_form, settings_form],
        "is_edit": False,
    })


@login_required
def news_edit(request, pk):
    post = get_object_or_404(News, pk=pk)

    if request.method == "POST":
        core_form = NewsCoreForm(request.POST, request.FILES, instance=post, prefix="core")
        seo_form = NewsSEOForm(request.POST, instance=post, prefix="seo")
        social_form = NewsSocialForm(request.POST, request.FILES, instance=post, prefix="social")
        settings_form = NewsSettingsForm(request.POST, instance=post, prefix="settings")

        forms = [core_form, seo_form, social_form, settings_form]

        if all(f.is_valid() for f in forms):
            news = core_form.save(commit=False)
            news.status = "published" if "publish" in request.POST else "draft"
            news.save()

            # ✅ TaggableManager handled by TagField automatically
            core_form.save_m2m()

            seo_form.save()
            social_form.save()
            settings_form.save()

            return redirect("dashboard:news_manager")
    else:
        core_form = NewsCoreForm(instance=post, prefix="core")
        seo_form = NewsSEOForm(instance=post, prefix="seo")
        social_form = NewsSocialForm(instance=post, prefix="social")
        settings_form = NewsSettingsForm(instance=post, prefix="settings")

    return render(request, "dashboard/news_form.html", {
        "core_form": core_form,
        "seo_form": seo_form,
        "social_form": social_form,
        "settings_form": settings_form,
        "all_forms": [core_form, seo_form, social_form, settings_form],
        "is_edit": True,
        "post": post,
    })



@login_required
def news_delete(request, pk):
    post = get_object_or_404(News, pk=pk)
    if request.method == "POST":
        post.delete()
    return redirect("dashboard:news_manager")


@login_required
def news_publish(request, pk):
    post = get_object_or_404(News, pk=pk)
    if request.method == "POST":
        post.status = "published"
        post.save()
    return redirect("dashboard:news_manager")



@login_required
def standings_manager(request):
    match_type = request.GET.get('match_type', 'division_two')
    season_id = request.GET.get('season')

    # If no season is selected, default to current
    if season_id:
        season = get_object_or_404(Season, id=season_id)
    else:
        season = get_current_season()

    standings = Standing.objects.filter(
        match_type=match_type,
        season=season
    )

    standings = sorted(
        standings,
        key=lambda s: (s.points, s.goal_difference, s.goal_for, -s.goal_against),
        reverse=True
    )

    for idx, s in enumerate(standings, start=1):
        s.position = idx

    match_type_display = dict(Standing.MATCH_TYPE_CHOICES).get(match_type, match_type)

    return render(request, "dashboard/standings_manager.html", {
        "standings": standings,
        "match_type_choices": Standing.MATCH_TYPE_CHOICES,
        "season_choices": Season.objects.all(),  # ✅ Use DB seasons
        "selected_match_type": match_type,
        "selected_season": season.id,  # ✅ Pass season.id
        "selected_match_type_display": match_type_display,
    })




@login_required
def manage_standings(request):
    # Get match type and season from query params
    match_type = request.GET.get("match_type", "division_two")
    season_id = request.GET.get("season")

    # Default to current season if no season selected
    if season_id:
        season = get_object_or_404(Season, id=season_id)
    else:
        season = get_current_season()

    # Fetch standings
    standings = Standing.objects.filter(
        match_type=match_type,
        season=season
    )

    # Sort standings
    sorted_standings = sorted(
        standings,
        key=lambda s: (s.points, s.goal_difference, s.goal_for, -s.goal_against),
        reverse=True
    )

    standings_with_positions = []
    for idx, standing in enumerate(sorted_standings, start=1):
        standings_with_positions.append({
            'standing': standing,
            'position': idx
        })

    if request.method == "POST":
        form = StandingForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            played = data['won'] + data['drawn'] + data['lost']

            standing, created = Standing.objects.update_or_create(
                team=data['team'],
                match_type=data['match_type'],
                season=data['season'],
                defaults={
                    "played": played,
                    "won": data['won'],
                    "drawn": data['drawn'],
                    "lost": data['lost'],
                    "goal_for": data['goal_for'],
                    "goal_against": data['goal_against'],
                }
            )

            return redirect(f"{request.path}?match_type={match_type}&season={season.id}")
    else:
        form = StandingForm(initial={"season": season, "match_type": match_type})

    return render(request, "dashboard/standings_form.html", {
        "standings_with_positions": standings_with_positions,
        "form": form,
        "selected_season": season.id,  # ✅ Pass ID, not string
        "selected_match_type": match_type,
        "season_choices": Season.objects.all(),  # ✅ Pass queryset
        "match_type_choices": Standing.MATCH_TYPE_CHOICES,
    })

@login_required
def standings_edit(request, pk):
    standing = get_object_or_404(Standing, pk=pk)

    if request.method == "POST":
        form = StandingForm(request.POST, instance=standing)
        if form.is_valid():
            data = form.cleaned_data
            played = data['won'] + data['drawn'] + data['lost']

            # Save with recalculated "played"
            standing = form.save(commit=False)
            standing.played = played
            standing.save()

            messages.success(request, f"✅ Standing for {standing.team.name} updated successfully.")

            # Redirect back to standings_manager, preserving filters
            match_type = standing.match_type
            season_id = standing.season.id
            return redirect(f"{reverse('dashboard:standings_manager')}?match_type={match_type}&season={season_id}")
    else:
        form = StandingForm(instance=standing)

    return render(request, "dashboard/standings_form.html", {
        "form": form,
        "standing": standing,
        "season_choices": Season.objects.all(),
        "match_type_choices": Standing.MATCH_TYPE_CHOICES,
    })



@login_required
def standings_delete(request, pk):
    standing = get_object_or_404(Standing, pk=pk)

    # Get current filters from request
    match_type = request.GET.get("match_type", "division_two")
    season_id = request.GET.get("season")

    if request.method == "POST":
        standing.delete()
        messages.success(request, f"✅ Standing for {standing.team.name} deleted successfully.")

        redirect_url = f"{reverse('dashboard:standings_manager')}?match_type={match_type}"
        if season_id:
            redirect_url += f"&season={season_id}"
        return redirect(redirect_url)

    # If someone hits GET directly, redirect back safely
    return redirect("dashboard:standings_manager")



@login_required
def analytics_dashboard(request):
    # Date range - last 7 days
    end_date = timezone.now()
    start_date = end_date - timedelta(days=7)
    
    # EXCLUDE analytics/dashboard URLs from all queries
    excluded_paths = [
        '/analytics/',
        '/dashboard/',
        '/admin/',
        '/static/',
        '/media/',
    ]
    
    # Basic metrics - EXCLUDE analytics URLs
    total_visits = PageView.objects.filter(
        timestamp__range=(start_date, end_date)
    ).exclude(
        Q(url__startswith='/analytics/') |
        Q(url__startswith='/dashboard/') |
        Q(url__startswith='/admin/') |
        Q(url__startswith='/static/') |
        Q(url__startswith='/media/')
    ).count()
    
    # Get sessions that only visited your tracked pages (not analytics)
    valid_sessions = PageView.objects.filter(
        timestamp__range=(start_date, end_date)
    ).exclude(
        Q(url__startswith='/analytics/') |
        Q(url__startswith='/dashboard/') |
        Q(url__startswith='/admin/') |
        Q(url__startswith='/static/') |
        Q(url__startswith='/media/')
    ).values_list('visitor_session_id', flat=True).distinct()
    
    unique_visitors = VisitorSession.objects.filter(
        id__in=valid_sessions,
        start_time__range=(start_date, end_date)
    ).count()
    
    # Bounce rate calculation - only for valid sessions
    bounce_sessions = VisitorSession.objects.filter(
        id__in=valid_sessions,
        start_time__range=(start_date, end_date)
    ).annotate(
        page_count=Count('page_views')
    ).filter(page_count=1).count()
    
    bounce_rate = round((bounce_sessions / unique_visitors * 100) if unique_visitors > 0 else 0, 1)
    
    # Average session duration - only for valid sessions
    avg_duration_result = VisitorSession.objects.filter(
        id__in=valid_sessions,
        start_time__range=(start_date, end_date),
        end_time__isnull=False
    ).annotate(
        duration=ExpressionWrapper(F('end_time') - F('start_time'), output_field=DurationField())
    ).aggregate(avg_duration=Avg('duration'))
    
    avg_duration = avg_duration_result['avg_duration'] or timedelta(0)
    avg_duration_minutes = round(avg_duration.total_seconds() / 60, 1) if avg_duration else 0
    
    # New vs returning visitors - only for valid sessions
    returning_visitors = VisitorSession.objects.filter(
        id__in=valid_sessions,
        start_time__range=(start_date, end_date)
    ).values('ip_address').annotate(count=Count('id')).filter(count__gt=1).count()
    
    new_visitors = unique_visitors - returning_visitors
    
    # Daily data for chart - EXCLUDE analytics URLs
    daily_data = PageView.objects.filter(
        timestamp__range=(start_date, end_date)
    ).exclude(
        Q(url__startswith='/analytics/') |
        Q(url__startswith='/dashboard/') |
        Q(url__startswith='/admin/') |
        Q(url__startswith='/static/') |
        Q(url__startswith='/media/')
    ).annotate(
        day=TruncDate('timestamp')
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    # Top pages - EXCLUDE analytics URLs
    top_pages = PageView.objects.filter(
        timestamp__range=(start_date, end_date)
    ).exclude(
        Q(url__startswith='/analytics/') |
        Q(url__startswith='/dashboard/') |
        Q(url__startswith='/admin/') |
        Q(url__startswith='/static/') |
        Q(url__startswith='/media/')
    ).values('url').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Section breakdown - already filtered by specific URLs
    section_breakdown = {
        'Home': PageView.objects.filter(timestamp__range=(start_date, end_date), url='/').count(),
        'News': PageView.objects.filter(timestamp__range=(start_date, end_date), url__startswith='/news/').count(),
        'Players': PageView.objects.filter(timestamp__range=(start_date, end_date), url__startswith='/players/').count(),
        'Standings': PageView.objects.filter(timestamp__range=(start_date, end_date), url__startswith='/standings/').count(),
    }
    
    # --- Helper function for traffic sources ---
    def count_referrers(*queries):
        """Utility to count pageviews with one or more Q queries combined."""
        q_obj = Q()
        for q in queries:
            q_obj |= q
        return PageView.objects.filter(
            timestamp__range=(start_date, end_date)
        ).exclude(
            Q(url__startswith='/analytics/') |
            Q(url__startswith='/dashboard/') |
            Q(url__startswith='/admin/') |
            Q(url__startswith='/static/') |
            Q(url__startswith='/media/')
        ).filter(q_obj).count()
    
    # Traffic sources - EXCLUDE analytics URLs
    traffic_sources = {
        'Direct': PageView.objects.filter(
            timestamp__range=(start_date, end_date),
            referrer__isnull=True
        ).exclude(
            Q(url__startswith='/analytics/') |
            Q(url__startswith='/dashboard/') |
            Q(url__startswith='/admin/') |
            Q(url__startswith='/static/') |
            Q(url__startswith='/media/')
        ).count(),
        'Search': count_referrers(
            Q(referrer__icontains='google'),
            Q(referrer__icontains='bing'),
            Q(referrer__icontains='yahoo'),
            Q(referrer__icontains='duckduckgo')
        ),
        'Social': count_referrers(
            Q(referrer__icontains='facebook'),
            Q(referrer__icontains='twitter'),
            Q(referrer__icontains='instagram'),
            Q(referrer__icontains='linkedin')
        ),
        'Email': count_referrers(
            Q(referrer__icontains='mail.'),
            Q(referrer__icontains='email'),
            Q(referrer__icontains='newsletter')
        ),
        'Other': PageView.objects.filter(
            timestamp__range=(start_date, end_date),
            referrer__isnull=False
        ).exclude(
            Q(url__startswith='/analytics/') |
            Q(url__startswith='/dashboard/') |
            Q(url__startswith='/admin/') |
            Q(url__startswith='/static/') |
            Q(url__startswith='/media/') |
            Q(referrer__icontains='google') |
            Q(referrer__icontains='bing') |
            Q(referrer__icontains='yahoo') |
            Q(referrer__icontains='duckduckgo') |
            Q(referrer__icontains='facebook') |
            Q(referrer__icontains='twitter') |
            Q(referrer__icontains='instagram') |
            Q(referrer__icontains='linkedin') |
            Q(referrer__icontains='mail.') |
            Q(referrer__icontains='email') |
            Q(referrer__icontains='newsletter')
        ).count()
    }
    
    # Device types - only for valid sessions
    device_types = VisitorSession.objects.filter(
        id__in=valid_sessions,
        start_time__range=(start_date, end_date)
    ).values('device_type').annotate(
        count=Count('id')
    )
    device_types_dict = {d['device_type']: d['count'] for d in device_types}
    
    # Top browsers - only for valid sessions
    top_browsers = VisitorSession.objects.filter(
        id__in=valid_sessions,
        start_time__range=(start_date, end_date)
    ).values('browser').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Top operating systems - only for valid sessions
    top_os = VisitorSession.objects.filter(
        id__in=valid_sessions,
        start_time__range=(start_date, end_date)
    ).values('operating_system').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Real-time active visitors (last 5 minutes) - only for valid sessions
    active_visitors = VisitorSession.objects.filter(
        id__in=valid_sessions,
        end_time__gte=timezone.now() - timedelta(minutes=5)
    ).count()
    
    context = {
        'total_visits': total_visits,
        'unique_visitors': unique_visitors,
        'bounce_rate': bounce_rate,
        'avg_duration': avg_duration_minutes,
        'new_visitors': new_visitors,
        'returning_visitors': returning_visitors,
        'active_visitors': active_visitors,
        'daily_data': list(daily_data),
        'top_pages': list(top_pages),
        'section_breakdown': section_breakdown,
        'traffic_sources': traffic_sources,
        'device_types': device_types_dict,
        'top_browsers': list(top_browsers),
        'top_os': list(top_os),
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, "dashboard/analytics_dashboard.html", context)




def settings_general(request):
    settings_instance = ClubGeneralSettings.objects.first()
    form = ClubGeneralSettingsForm(instance=settings_instance)
    
    # Instantiate empty formsets for display only (no POST processing here)
    SocialFormset = inlineformset_factory(
        ClubGeneralSettings,
        SocialLink,
        form=SocialLinkForm,
        extra=0,
        can_delete=True
    )
    social_formset = SocialFormset(instance=settings_instance, prefix='social')

    MenuFormset = inlineformset_factory(
        ClubGeneralSettings,
        MenuItem,
        form=MenuItemForm,
        extra=0,
        can_delete=True
    )
    menu_formset = MenuFormset(instance=settings_instance, prefix='menu')

    return render(request, 'dashboard/settings_general.html', {
        'form': form,
        'social_formset': social_formset,
        'menu_formset': menu_formset,
    })


def update_club_settings(request):
    settings_instance = ClubGeneralSettings.objects.first()
    if request.method == 'POST':
        form = ClubGeneralSettingsForm(request.POST, request.FILES, instance=settings_instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Club general settings updated successfully!")
            return redirect('dashboard:settings_general')
        else:
            messages.error(request, "Please correct the errors in the club settings form.")
    else:
        form = ClubGeneralSettingsForm(instance=settings_instance)

    # Provide empty formsets for rendering so template renders properly
    SocialFormset = inlineformset_factory(
        ClubGeneralSettings,
        SocialLink,
        form=SocialLinkForm,
        extra=0,
        can_delete=True
    )
    social_formset = SocialFormset(instance=settings_instance, prefix='social')

    MenuFormset = inlineformset_factory(
        ClubGeneralSettings,
        MenuItem,
        form=MenuItemForm,
        extra=0,
        can_delete=True
    )
    menu_formset = MenuFormset(instance=settings_instance, prefix='menu')

    return render(request, 'dashboard/settings_general.html', {
        'form': form,
        'social_formset': social_formset,
        'menu_formset': menu_formset,
    })


def update_social_links(request):
    settings_instance = ClubGeneralSettings.objects.first()
    SocialFormset = inlineformset_factory(
        ClubGeneralSettings,
        SocialLink,
        form=SocialLinkForm,
        extra=0,
        can_delete=True
    )

    if request.method == 'POST':
        formset = SocialFormset(request.POST, instance=settings_instance, prefix='social')
        if formset.is_valid():
            formset.save()
            messages.success(request, "Social links updated successfully!")
            return redirect('dashboard:settings_general')
        else:
            messages.error(request, "Please correct the errors in social links.")
    else:
        formset = SocialFormset(instance=settings_instance, prefix='social')

    # Provide empty form and menu_formset for full template rendering
    form = ClubGeneralSettingsForm(instance=settings_instance)
    MenuFormset = inlineformset_factory(
        ClubGeneralSettings,
        MenuItem,
        form=MenuItemForm,
        extra=0,
        can_delete=True
    )
    menu_formset = MenuFormset(instance=settings_instance, prefix='menu')

    return render(request, 'dashboard/settings_general.html', {
        'form': form,
        'social_formset': formset,
        'menu_formset': menu_formset,
    })


def update_menu_items(request):
    settings_instance = ClubGeneralSettings.objects.first()
    MenuFormset = inlineformset_factory(
        ClubGeneralSettings,
        MenuItem,
        form=MenuItemForm,
        extra=0,
        can_delete=True
    )

    if request.method == 'POST':
        formset = MenuFormset(request.POST, instance=settings_instance, prefix='menu')
        if formset.is_valid():
            formset.save()
            messages.success(request, "Menu items updated successfully!")
            return redirect('dashboard:settings_general')
        else:
            messages.error(request, "Please correct the errors in menu items.")
    else:
        formset = MenuFormset(instance=settings_instance, prefix='menu')

    # Provide empty form and social_formset for full template rendering
    form = ClubGeneralSettingsForm(instance=settings_instance)
    SocialFormset = inlineformset_factory(
        ClubGeneralSettings,
        SocialLink,
        form=SocialLinkForm,
        extra=0,
        can_delete=True
    )
    social_formset = SocialFormset(instance=settings_instance, prefix='social')

    return render(request, 'dashboard/settings_general.html', {
        'form': form,
        'social_formset': social_formset,
        'menu_formset': formset,
    })

@login_required
def social_delete(request, pk):
    social = get_object_or_404(SocialLink, pk=pk)
    # optional: ensure only your club's socials can be deleted
    if hasattr(request.user, "club") and social.club != request.user.club:
        messages.error(request, "You cannot delete this social link.")
        return redirect(reverse("dashboard:settings_general"))

    social.delete()
    messages.success(request, f"{social.platform.title()} link removed.")
    return redirect(reverse("dashboard:settings_general"))



@login_required
def menu_delete(request, pk):
    """Delete a menu item"""
    menu_item = get_object_or_404(MenuItem, pk=pk)
    
    # Optional: ensure only your club's menu items can be deleted
    if hasattr(request.user, "club") and menu_item.settings != request.user.club:
        messages.error(request, "You cannot delete this menu item.")
        return redirect(reverse("dashboard:settings_general"))

    menu_item.delete()
    messages.success(request, f'Menu item "{menu_item.label}" has been deleted successfully.')
    return redirect(reverse("dashboard:settings_general"))



from matches.models import Match


@login_required
def settings_team(request):
    roles = ClubRole.objects.all()
    members = ClubTeamMember.objects.select_related("role", "user_account")

    role_form = ClubRoleForm()
    member_form = ClubTeamMemberForm()
    cms_form = AssignCMSUserForm()
    player_form = PlayerForm()

    players = Player.objects.all()

    # ✅ pick the most recent match in the current season
    season = get_current_season()
    match = Match.objects.filter(season=season).order_by("-date").first()

    return render(
        request,
        "dashboard/settings_team.html",
        {
            "roles": roles,
            "members": members,
            "role_form": role_form,
            "member_form": member_form,
            "cms_form": cms_form,
            "player_form": player_form,
            "players": players,
            "match": match,   # ✅ pass it here
        },
    )



@login_required
def create_role(request):
    if request.method == "POST":
        form = ClubRoleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Role created successfully.")
    return redirect("dashboard:settings_team")


@login_required
def create_team_member(request):
    if request.method == "POST":
        form = ClubTeamMemberForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Team member added successfully.")
    return redirect("dashboard:settings_team")


@login_required
def assign_cms_user(request):
    if request.method == "POST":
        form = AssignCMSUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "CMS user linked successfully.")
    return redirect("dashboard:settings_team")


@login_required
def delete_team_member(request, member_id):
    member = get_object_or_404(ClubTeamMember, id=member_id)
    member.delete()
    messages.success(request, f"Team member {member.full_name} removed successfully.")
    return redirect("dashboard:settings_team")


@login_required
def edit_team_member(request, member_id):
    member = get_object_or_404(ClubTeamMember, id=member_id)

    if request.method == "POST":
        form = ClubTeamMemberForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, f"{member.full_name} updated successfully.")
            return redirect("dashboard:settings_team")
    else:
        form = ClubTeamMemberForm(instance=member)

    return render(
        request,
        "dashboard/settings_team_edit.html",
        {"form": form, 
         "member": member,
         'current_member': ClubTeamMember.objects.filter(user_account=request.user).first(),
        },
    )


@login_required
def settings_integrations(request):
    settings = ClubIntegrationSettings.objects.first()
    if request.method == "POST":
        form = ClubIntegrationSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            return redirect("dashboard:settings_integrations")
    else:
        form = ClubIntegrationSettingsForm(instance=settings)
    return render(request, "dashboard/settings_integrations.html", {"form": form})
