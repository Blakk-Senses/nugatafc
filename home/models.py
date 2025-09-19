from django.shortcuts import render
from news.models import News
from players.models import Player
from matches.models import Match

def home(request):
    latest_news = News.objects.order_by("-created_at")[:3]  # latest 3 posts
    next_fixture = Match.objects.filter(status="upcoming").order_by("date").first()
    featured_player = Player.objects.first()  # you can later add a "featured" flag

    return render(request, "home/home.html", {
        "latest_news": latest_news,
        "next_fixture": next_fixture,
        "featured_player": featured_player,
    })
