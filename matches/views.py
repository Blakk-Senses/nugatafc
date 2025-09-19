"""
Views for managing teams, matches, and seasons in the club management app.

This module handles:
- Viewing matches per season or overall (home page display).
- Managing teams (CRUD operations).
- Managing matches (CRUD operations and results entry).
- Returning match info as JSON (for AJAX requests).

Dependencies:
    - Django shortcuts, messages, authentication decorators
    - Models: Team, Match, Standing, ClubGeneralSettings, Season
    - Forms: TeamForm, MatchForm, MatchResultForm
"""

from django.conf import settings
from django.db.models import Q
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Team, Match, Standing
from dashboard.models import ClubGeneralSettings
from .forms import TeamForm, MatchForm, MatchResultForm
from django.http import JsonResponse
from dashboard.models import Season, get_current_season


def season_matches(request):
    """
    Display matches for the selected season or show recent/upcoming matches.

    - If a season is selected (via query param ?season=<id>), show all matches 
      involving the current club in that season.
    - Otherwise, show the last 5 finished matches + all upcoming matches.

    Args:
        request (HttpRequest): The incoming request.

    Returns:
        HttpResponse: Rendered "home/season_matches.html".
    """
    # ✅ Fetch general club settings
    settings_instance = ClubGeneralSettings.objects.first()
    if not settings_instance:
        messages.error(request, "Club settings are not configured.")
        return redirect("dashboard:settings_general")

    club_name = settings_instance.club_name

    # Available seasons for dropdown
    seasons = Season.objects.all().order_by("-start_date")
    selected_season_id = request.GET.get("season")
    selected_season = None

    # Check if a valid season is selected
    if selected_season_id:
        try:
            selected_season = Season.objects.get(id=selected_season_id)
        except Season.DoesNotExist:
            selected_season = None

    if selected_season:
        # Matches in the chosen season involving this club
        matches = (
            Match.objects.filter(season=selected_season)
            .filter(Q(home_team__name=club_name) | Q(away_team__name=club_name))
            .order_by("date")
        )
    else:
        # Default: recent + upcoming matches
        last_5_finished = (
            Match.objects.filter(status="finished")
            .filter(Q(home_team__name=club_name) | Q(away_team__name=club_name))
            .order_by("-date")[:5]
        )
        upcoming = (
            Match.objects.filter(status="upcoming")
            .filter(Q(home_team__name=club_name) | Q(away_team__name=club_name))
            .order_by("date")
        )

        matches = list(last_5_finished) + list(upcoming)
        matches = sorted(matches, key=lambda m: m.date)

    return render(request, "home/season_matches.html", {
        "seasons": seasons,
        "selected_season": selected_season,
        "matches": matches,
        "club_name": club_name,
        "club_settings": settings_instance,  # crest, colors, etc.
    })


# -----------------------------------------------------------------------------


@login_required
def team_manager(request):
    """
    List all teams for management.

    Returns:
        HttpResponse: Rendered "dashboard/team_manager.html".
    """
    teams = Team.objects.all().order_by("name")
    return render(request, "dashboard/team_manager.html", {"teams": teams})


@login_required
def team_create(request, team_id=None):
    """
    Create or edit a team.

    - If team_id is provided, edit that team (unless it’s the club’s own team).
    - On POST: validate and save the team (handle logo upload/removal).
    - On GET: show a form (prefilled for edit or with default season for new).

    Args:
        request (HttpRequest): Request object.
        team_id (int, optional): Team ID to edit.

    Returns:
        HttpResponse: Rendered "dashboard/team_form.html".
    """
    if team_id:
        team = get_object_or_404(Team, id=team_id)

        # Prevent editing your own club team here
        settings = ClubGeneralSettings.objects.first()
        if settings and team.name == settings.club_name:
            messages.info(request, "Edit your own club details in Settings → General.")
            return redirect("dashboard:settings_general")
    else:
        team = None

    if request.method == "POST":
        form = TeamForm(request.POST, request.FILES, instance=team)
        if form.is_valid():
            team = form.save(commit=False)

            # Handle logo removal
            if request.POST.get("remove_logo") == "true" and team.logo:
                team.logo.delete(save=False)
                team.logo = None

            # Handle new logo upload
            if "logo" in request.FILES:
                team.logo = request.FILES["logo"]

            team.save()
            return redirect("dashboard:team_manager")
    else:
        if team:
            form = TeamForm(instance=team)
        else:
            current_season_id = get_current_season()
            form = TeamForm(initial={"season": current_season_id})

    return render(request, "dashboard/team_form.html", {
        "form": form,
        "is_edit": bool(team),
        "team": team
    })


@login_required
def team_edit(request, pk):
    """
    Edit a team (simplified version of team_create).

    Args:
        request (HttpRequest)
        pk (int): Team primary key.

    Returns:
        HttpResponse: Rendered "dashboard/team_form.html".
    """
    team = get_object_or_404(Team, pk=pk)
    if request.method == "POST":
        form = TeamForm(request.POST, request.FILES, instance=team)
        if form.is_valid():
            form.save()
            return redirect("dashboard:team_manager")
    else:
        form = TeamForm(instance=team)
    return render(request, "dashboard/team_form.html", {"form": form, "is_edit": True, "team": team})


@login_required
def team_delete(request, team_id):
    """
    Delete a team (except the club’s own team).

    Args:
        request (HttpRequest)
        team_id (int): Team ID.

    Returns:
        HttpResponseRedirect: Redirects to team manager.
    """
    team = get_object_or_404(Team, id=team_id)
    settings = ClubGeneralSettings.objects.first()

    if settings and team.name == settings.club_name:
        messages.error(request, "You cannot delete your own club team.")
        return redirect("dashboard:team_manager")

    team.delete()
    messages.success(request, "Team deleted successfully.")
    return redirect("dashboard:team_manager")


# -----------------------------------------------------------------------------


@login_required
def match_manager(request):
    """
    List all matches for management.

    Returns:
        HttpResponse: Rendered "dashboard/match_manager.html".
    """
    matches = Match.objects.all().order_by("-date")
    return render(request, "dashboard/match_manager.html", {"matches": matches})


@login_required
def manage_match(request):
    """
    Handle creation of upcoming matches or submission of results.

    - form_mode determines which form is used ("upcoming" or "results").
    - Upcoming: create a new match in the current season.
    - Results: update scores for an existing upcoming match.

    Args:
        request (HttpRequest)

    Returns:
        HttpResponse: Rendered "dashboard/match_form.html".
    """
    matches_for_results = Match.objects.filter(status='upcoming').order_by('-date')
    current_season = get_current_season()

    form_mode = request.POST.get('form_mode', 'upcoming')
    match_form = MatchForm(initial={"season": current_season})
    result_form = MatchResultForm()
    result_form.fields['match_selector'].queryset = matches_for_results

    if request.method == "POST":
        if form_mode == 'upcoming':
            match_form = MatchForm(request.POST)
            if match_form.is_valid():
                match_form.save()
                return redirect("dashboard:match_manager")

        elif form_mode == 'results':
            result_form = MatchResultForm(request.POST)
            result_form.fields['match_selector'].queryset = matches_for_results
            if result_form.is_valid():
                result_form.save()
                return redirect("dashboard:match_manager")

    return render(request, "dashboard/match_form.html", {
        "match_form": match_form,
        "result_form": result_form,
        "form_mode": form_mode,
        "is_edit": False,
        "matches_for_results": matches_for_results,
        "current_season": current_season,
    })


@login_required
def match_edit(request, pk):
    """
    Edit match details (but keep its status unchanged).

    Args:
        request (HttpRequest)
        pk (int): Match ID.

    Returns:
        HttpResponse: Rendered "dashboard/match_form.html".
    """
    match = get_object_or_404(Match, pk=pk)
    
    if request.method == "POST":
        match_form = MatchForm(request.POST, instance=match)
        if match_form.is_valid():
            m = match_form.save(commit=False)
            m.status = match.status  # preserve match status
            m.save()
            return redirect("dashboard:match_manager")
    else:
        match_form = MatchForm(instance=match)

    return render(request, "dashboard/match_form.html", {
        "match_form": match_form,
        "result_form": MatchResultForm(),
        "is_edit": True,
        "match": match,
        "form_mode": "upcoming",
        "current_season": match.season,
    })


@login_required
def match_delete(request, pk):
    """
    Delete a match and revert standings if it was finished.

    Args:
        request (HttpRequest)
        pk (int): Match ID.

    Returns:
        HttpResponseRedirect: Redirects to match manager.
    """
    match = get_object_or_404(Match, pk=pk)

    # Revert standings update if match was finished
    if match.status == "finished":
        for team, goals_for, goals_against in [
            (match.home_team, match.home_score, match.away_score),
            (match.away_team, match.away_score, match.home_score),
        ]:
            standing = Standing.objects.get(
                team=team, 
                match_type=match.match_type, 
                season=match.season
            )
            standing.played -= 1
            standing.goal_for -= goals_for
            standing.goal_against -= goals_against

            if goals_for > goals_against:
                standing.won -= 1
                standing.points -= 3
            elif goals_for < goals_against:
                standing.lost -= 1
            else:
                standing.drawn -= 1
                standing.points -= 1

            standing.goal_difference = standing.goal_for - standing.goal_against
            standing.save()

    match.delete()
    return redirect("dashboard:match_manager")


@login_required
def match_info(request, match_id):
    """
    Return match info as JSON (used for AJAX requests).

    Args:
        request (HttpRequest)
        match_id (int): Match ID.

    Returns:
        JsonResponse: Match details or error message.
    """
    try:
        match = Match.objects.get(id=match_id)
        return JsonResponse({
            'home_team': str(match.home_team),
            'away_team': str(match.away_team),
            'date': match.date.strftime('%Y-%m-%d %H:%M'),
            'location': match.location,
            'match_type': match.get_match_type_display(),
            'season': match.season,
        })
    except Match.DoesNotExist:
        return JsonResponse({'error': 'Match not found'}, status=404)
