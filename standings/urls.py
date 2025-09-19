from django.urls import path
from standings.views import full_standings

app_name = "standings"

urlpatterns = [
    path("full/", full_standings, name="full_standings"),
]
