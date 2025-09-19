from django.shortcuts import render
from matches.models import Standing
from django.shortcuts import get_object_or_404
from dashboard.models import Season, get_current_season


def full_standings(request):
    # --- inputs ---
    match_type = request.GET.get("match_type", "division_two")
    selected_season_id = request.GET.get("season")

    # --- available seasons for this match_type ---
    available_seasons = (
        Season.objects.filter(standings__match_type=match_type)
        .distinct()
        .order_by("-start_date")
    )

    # --- pick season ---
    if selected_season_id:
        season = get_object_or_404(Season, id=selected_season_id)
    else:
        season = available_seasons.first()
        if not season:
            season = get_current_season()

    # --- standings queryset ---
    standings = Standing.objects.filter(
        match_type=match_type,
        season=season,
    )

    # --- calculate points & GD ---
    for s in standings:
        s.points = s.won * 3 + s.drawn
        s.goal_difference = s.goal_for - s.goal_against

    # --- sort standings ---
    standings = sorted(
        standings,
        key=lambda s: (s.points, s.goal_difference, s.goal_for, -s.goal_against),
        reverse=True,
    )

    # --- assign positions ---
    for idx, s in enumerate(standings, start=1):
        s.position = idx

    # --- match type display ---
    match_type_display = dict(Standing.MATCH_TYPE_CHOICES).get(match_type, match_type)

    return render(request, "home/full_standings.html", {
        "standings": standings,
        "match_type_choices": Standing.MATCH_TYPE_CHOICES,
        "season_choices": available_seasons,   # ✅ only relevant seasons
        "selected_match_type": match_type,
        "selected_season": season,
        "selected_match_type_display": match_type_display,
    })

