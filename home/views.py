from django.shortcuts import render
from django.db.models import Q
from django.conf import settings
from matches.models import Match, Standing
from news.models import News


def home(request):
    """
    Public homepage view.

    Responsibilities:
    - Show the next 3 upcoming matches involving the configured team.
    - Show the last 3 finished matches involving the configured team.
    - Display the top 5 league standings (with calculated position).
    - Show the latest 3 published news posts.

    Context provided to the template:
    - upcoming_matches: Queryset of the next 3 matches.
    - recent_results: Queryset of the last 3 finished matches.
    - standings: Top 5 standings with calculated_position added dynamically.
    - latest_news: Latest 3 published news articles.
    """

    # Team name (configurable in settings.py, defaults to 'Nugata FC')
    team_name = getattr(settings, "TEAM_NAME", "Nugata FC")

    # --- Upcoming Matches ---
    upcoming_matches = (
        Match.objects.filter(status="upcoming")
        .filter(Q(home_team__name=team_name) | Q(away_team__name=team_name))
        .order_by("date")[:3]  # Next 3 matches
    )

    # --- Recent Results ---
    recent_results = (
        Match.objects.filter(status="finished")
        .filter(Q(home_team__name=team_name) | Q(away_team__name=team_name))
        .order_by("-date")[:3]  # Last 3 finished matches
    )

    # --- Standings (Top 5) ---
    all_standings = Standing.objects.all()

    # Sort standings by multiple criteria:
    # Priority: points > goal_difference > goals_for > goals_against (ascending)
    sorted_standings = sorted(
        all_standings,
        key=lambda s: (s.points, s.goal_difference, s.goal_for, -s.goal_against),
        reverse=True,
    )

    # Dynamically assign calculated_position (only for top 5)
    for idx, standing in enumerate(sorted_standings[:5], start=1):
        standing.calculated_position = idx

    # --- Latest News ---
    latest_news = (
        News.objects.filter(status="published")
        .order_by("-created_at")[:3]  # Latest 3 posts
    )

    # --- Render template ---
    return render(
        request,
        "home/homepage.html",
        {
            "upcoming_matches": upcoming_matches,
            "recent_results": recent_results,
            "standings": sorted_standings[:5],
            "latest_news": latest_news,
        },
    )
