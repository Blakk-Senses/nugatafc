from django.urls import path
from players.views import team_view, player_detail

app_name = "players"

urlpatterns = [
    path("", team_view, name="team_view"),
    path("<slug:slug>/", player_detail, name="player_detail"),
]
