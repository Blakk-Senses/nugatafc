from django.urls import path
from matches.views import season_matches

app_name = "matches"

urlpatterns = [
    path("", season_matches, name="season_matches"),
]




