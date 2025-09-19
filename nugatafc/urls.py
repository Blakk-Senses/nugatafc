from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("home.urls")),  
    path("news/", include("news.urls", namespace="news")),
    path("players/", include("players.urls", namespace="players")),
    path("matches/", include("matches.urls", namespace="matches")),
    path("dashboard/", include("dashboard.urls")), 
    path("standings/", include("standings.urls", namespace="standings")),
    path("ckeditor5/", include('django_ckeditor_5.urls')),
    
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)