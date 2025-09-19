"""
Player views module.

This file handles:
- Team overview display (players + staff by season).
- Player detail pages with aggregated stats.
- CRUD operations for players and their seasonal assignments.
- Managing and recording player match performances.

Dependencies:
    - Django shortcuts: render, get_object_or_404, redirect
    - Django contrib: login_required, messages
    - Django ORM: models, Q, aggregations
    - Project models: Player, PlayerSeason, PlayerMatchPerformance, Season, Match
    - Project forms: PlayerForm, PlayerSeasonForm, PlayerMatchPerformanceFormSet
"""

import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db import models
from django.db.models import (
    Sum, Count, Case, When, IntegerField, Q
)
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator

from dashboard.models import Season, get_current_season, StaffSeason
from .models import Player, PlayerSeason, PlayerMatchPerformance, MATCH_TYPE_CHOICES
from matches.models import Match
from players.forms import (
    PlayerForm, PlayerSeasonForm, PlayerMatchPerformanceFormSet
)

logger = logging.getLogger(__name__)


# ----------------- TEAM VIEW -----------------

def team_view(request):
    """
    Display current season team (players + staff).
    Players are sorted into groups (GK, defenders, midfielders, forwards),
    then by jersey number.
    """
    current_season = get_current_season()

    # Fetch all player seasons for the current season
    player_seasons = (
        PlayerSeason.objects.filter(season=current_season)
        .prefetch_related("positions", "player")
    )

    # Position grouping order
    ROLE_ORDER = {
        "GK": 1,
        "RB": 2, "LB": 2, "CB": 2,
        "DM": 3, "CM": 3, "AM": 3, "WG": 3,
        "FW": 4, "ST": 4,
    }

    def get_group(ps):
        """Return role group number for sorting."""
        for pos in ps.positions.all():
            if pos.code in ROLE_ORDER:
                return ROLE_ORDER[pos.code]
        return 99  # fallback group

    # Sort by group + jersey number
    player_seasons = sorted(
        player_seasons,
        key=lambda ps: (get_group(ps), ps.jersey_number or 999)
    )

    # Active staff for the season
    staff_assignments = StaffSeason.objects.filter(
        season=current_season,
        staff__date_joined__lte=current_season.end_date
    ).filter(
        Q(staff__date_left__isnull=True) |
        Q(staff__date_left__gte=current_season.start_date)
    ).select_related("staff")

    return render(request, "home/team.html", {
        "player_seasons": player_seasons,
        "staff_assignments": staff_assignments,
    })


# ----------------- PLAYER DETAIL -----------------

def player_detail(request, slug):
    """
    Display detailed stats for a player:
    - Aggregates performances (appearances, goals, assists, etc).
    - Allows filtering by season and match type.
    - Falls back to PlayerSeason stats if match data is missing.
    """
    player = get_object_or_404(Player, slug=slug)
    selected_match_type = request.GET.get("match_type", "division_two")
    selected_season_id = request.GET.get("season")

    logger.debug("player_detail called for player=%s (%s)", player.pk, player.full_name)

    # Available seasons for the player
    available_seasons = Season.objects.filter(player_seasons__player=player).distinct()

    # Pick season (priority: GET → latest with performances → latest available → current)
    if selected_season_id:
        season = get_object_or_404(Season, id=selected_season_id)
    else:
        season = (
            Season.objects.filter(
                player_seasons__performances__match_type=selected_match_type,
                player_seasons__player=player,
            )
            .distinct()
            .order_by("-start_date")
            .first()
        ) or available_seasons.order_by("-start_date").first() or get_current_season()

    # PlayerSeason for that season
    player_season = PlayerSeason.objects.filter(player=player, season=season).first()

    # Performances for that season/match type
    performances_qs = PlayerMatchPerformance.objects.filter(
        player_season__player=player,
        player_season__season=season,
        match_type=selected_match_type,
    )

    # Aggregated stats
    agg = performances_qs.aggregate(
        appearances=Coalesce(Count("id"), 0),
        minutes_played=Coalesce(Sum("minutes_played"), 0),
        goals=Coalesce(Sum("goals"), 0),
        assists=Coalesce(Sum("assists"), 0),
        clean_sheets=Coalesce(
            Sum(Case(When(clean_sheet=True, then=1), default=0, output_field=IntegerField())), 0
        ),
        big_chances_created=Coalesce(Sum("big_chances_created"), 0),
        tackles_won=Coalesce(Sum("tackles_won"), 0),
        clearances=Coalesce(Sum("clearances"), 0),
        penalties_taken=Coalesce(Sum("penalties_taken"), 0),
        penalties_scored=Coalesce(Sum("penalties_scored"), 0),
        penalties_saved=Coalesce(Sum("penalties_saved"), 0),
        saves=Coalesce(Sum("saves"), 0),
        yellow_cards=Coalesce(Sum("yellow_cards"), 0),
        red_cards=Coalesce(Sum("red_cards"), 0),
    )
    agg = {k: int(v or 0) for k, v in agg.items()}

    # Merge with PlayerSeason fallback
    final_stats = {}
    fallback_map = {
        "appearances": "appearances",
        "goals": "goals",
        "assists": "assists",
        "clean_sheets": "clean_sheets",
        "big_chances_created": "big_chances_created",
        "tackles_won": "tackles_won",
        "clearances": "clearances",
        "penalties_saved": "penalties_saved",
        "penalties_scored": "penalties_scored",
        "saves": "saves",
        "yellow_cards": "yellow_cards",
        "red_cards": "red_cards",
    }
    for key, value in agg.items():
        val = value
        if (val == 0 or val is None) and player_season:
            ps_field = fallback_map.get(key)
            if ps_field and hasattr(player_season, ps_field):
                val = getattr(player_season, ps_field) or 0
        final_stats[key] = int(val or 0)

    final_stats["performances_count"] = performances_qs.count()

    # Determine player role (for template display)
    player_role = None
    if player_season and player_season.positions.exists():
        pos_code = player_season.positions.first().code
        role_map = {
            "GK": "goalkeeper",
            "RB": "defender", "LB": "defender", "CB": "defender",
            "DM": "midfielder", "CM": "midfielder", "AM": "midfielder",
            "WG": "forward", "FW": "forward", "ST": "forward",
        }
        player_role = role_map.get(pos_code)

    return render(request, "home/player_detail.html", {
        "player": player,
        "player_season": player_season,
        "stats": final_stats,
        "match_types": MATCH_TYPE_CHOICES,
        "selected_match_type": selected_match_type,
        "available_seasons": available_seasons,
        "selected_season": season,
        "player_role": player_role,
    })


# ----------------- PLAYER CRUD -----------------

@login_required
def player_create(request):
    """Create a new player profile."""
    if request.method == "POST":
        form = PlayerForm(request.POST, request.FILES)
        if form.is_valid():
            player = form.save()
            messages.success(request, f"Player '{player.full_name}' created successfully.")
        else:
            messages.error(request, "Failed to create player. Please check the form.")
    return redirect("dashboard:settings_team")


@login_required
def player_edit(request, player_id):
    """Edit an existing player profile."""
    player = get_object_or_404(Player, id=player_id)
    if request.method == "POST":
        form = PlayerForm(request.POST, request.FILES, instance=player)
        if form.is_valid():
            form.save()
            messages.success(request, f"Player '{player.full_name}' updated successfully.")
            return redirect("dashboard:settings_team")
        messages.error(request, "Failed to update player. Please check the form.")
    else:
        form = PlayerForm(instance=player)

    return render(request, "dashboard/player_edit.html", {"form": form, "player": player})


@login_required
def player_delete(request, player_id):
    """Delete a player profile."""
    player = get_object_or_404(Player, id=player_id)
    player_name = player.full_name
    player.delete()
    messages.success(request, f"Player '{player_name}' deleted successfully.")
    return redirect("dashboard:settings_team")


# ----------------- PLAYER SEASON -----------------

@login_required
def player_manager(request):
    """Manage players assigned to seasons."""
    seasons = Season.objects.all().order_by("-start_date")
    season_id = request.GET.get("season")
    if season_id:
        season = Season.objects.filter(id=season_id).first() or get_current_season()
    else:
        season = get_current_season()

    player_seasons = PlayerSeason.objects.filter(season=season).select_related("player").prefetch_related("positions")

    return render(request, "dashboard/player_manager.html", {
        "seasons": seasons,
        "season": season,
        "player_seasons": player_seasons,
    })


@login_required
def manage_player(request, playerseason_id=None):
    """Assign or edit a player's season registration."""
    player_season = get_object_or_404(PlayerSeason, id=playerseason_id) if playerseason_id else None

    if request.method == "POST":
        form = PlayerSeasonForm(request.POST, instance=player_season)
        if form.is_valid():
            player_season = form.save(commit=False)
            if not playerseason_id:
                exists = PlayerSeason.objects.filter(
                    player=player_season.player, season=player_season.season
                ).exists()
                if exists:
                    messages.error(request, "This player is already assigned to that season.")
                    return redirect(f"{reverse('dashboard:player_manager')}?season={player_season.season.id}")
            player_season.save()
            form.save_m2m()
            messages.success(request, "Player assignment saved successfully.")
            return redirect(f"{reverse('dashboard:player_manager')}?season={player_season.season.id}")
    else:
        form = PlayerSeasonForm(instance=player_season)

    return render(request, "dashboard/player_form.html", {"form": form, "player_season": player_season})


@login_required
def delete_playerseason(request, pk):
    """Remove a player's assignment for a season."""
    player_season = get_object_or_404(PlayerSeason, pk=pk)
    season_id = player_season.season.id
    player_season.delete()
    messages.success(request, "Player assignment deleted successfully.")
    return redirect(f"{reverse('dashboard:player_manager')}?season={season_id}")


# ----------------- PLAYER MATCH PERFORMANCE -----------------

@login_required
def performance_list(request):
    """
    List matches with recorded performances (paginated).
    Allows filtering by season.
    """
    season = get_current_season()
    selected_season_id = request.GET.get("season")
    if selected_season_id:
        season = get_object_or_404(Season, id=selected_season_id)

    matches = (
        Match.objects.filter(season=season, status="finished")
        .filter(player_performances__isnull=False)
        .order_by("-date")
        .distinct()
    )

    paginator = Paginator(matches, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    all_seasons = Season.objects.all().order_by("-start_date")

    return render(request, "dashboard/performance_list.html", {
        "matches": page_obj,
        "current_season": season,
        "all_seasons": all_seasons,
    })


@login_required
def manage_performance(request, match_id=None):
    """
    Add/edit performances for a match.
    Ensures all season players are included in the match's performance records.
    """
    season = get_current_season()
    selected_match = None
    formset = None
    is_edit = False

    if match_id:
        # Edit mode
        selected_match = get_object_or_404(Match, id=match_id, season=season, status="finished")
        is_edit = True
        performances = PlayerMatchPerformance.objects.filter(match=selected_match)

        # Ensure new players are added to the match
        season_players = PlayerSeason.objects.filter(season=season)
        for ps in season_players:
            PlayerMatchPerformance.objects.get_or_create(
                player_season=ps,
                match=selected_match,
                defaults={"match_type": selected_match.match_type},
            )
        performances = PlayerMatchPerformance.objects.filter(match=selected_match)
    else:
        # Add mode
        match_id = request.GET.get("match") or request.POST.get("match")
        if match_id:
            selected_match = get_object_or_404(Match, id=match_id, season=season, status="finished")
            for ps in PlayerSeason.objects.filter(season=season):
                PlayerMatchPerformance.objects.get_or_create(
                    player_season=ps,
                    match=selected_match,
                    defaults={"match_type": selected_match.match_type},
                )
            performances = PlayerMatchPerformance.objects.filter(match=selected_match)
        else:
            performances = PlayerMatchPerformance.objects.none()

    if request.method == "POST":
        formset = PlayerMatchPerformanceFormSet(request.POST, queryset=performances)
        if formset.is_valid():
            formset.save()
            msg = "updated" if is_edit else "saved"
            messages.success(request, f"Performances for {selected_match} {msg} successfully.")
            return redirect("dashboard:performance_list")
        messages.error(request, "Please correct the errors below.")
    else:
        formset = PlayerMatchPerformanceFormSet(queryset=performances)

    matches = Match.objects.filter(season=season, status="finished").order_by("-date")

    return render(request, "dashboard/player_performance.html", {
        "matches": matches,
        "selected_match": selected_match,
        "formset": formset,
        "is_edit": is_edit,
    })


@login_required
def performance_delete(request, match_id):
    """Delete all performances for a given match."""
    match = get_object_or_404(Match, id=match_id, status="finished")
    if request.method == "POST":
        PlayerMatchPerformance.objects.filter(match=match).delete()
        messages.success(request, f"Performances for {match} deleted.")
    return redirect("dashboard:performance_list")
