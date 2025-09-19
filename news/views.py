"""
Views for displaying news articles in the home app.

This module provides:
- A list view showing all published news posts.
- A detail view showing a single news article along with related posts.

Dependencies:
    - Django shortcuts (render, get_object_or_404)
    - News model (with status, tags, category, slug, created_at fields)
"""

from django.shortcuts import render, get_object_or_404
from .models import News


def news_list(request):
    """
    Display a list of published news articles.

    - Fetches all News objects with status="published".
    - Orders them by most recent first (descending created_at).

    Args:
        request (HttpRequest): The incoming request.

    Returns:
        HttpResponse: Rendered "home/news_list.html" with posts context.
    """
    posts = News.objects.filter(status="published").order_by("-created_at")
    return render(request, "home/news_list.html", {"posts": posts})


def news_detail(request, slug):
    """
    Display a single news article with related articles.

    - Fetches a News object by its slug (only if published).
    - If the post has tags:
        → Find up to 3 related posts sharing at least one tag.
    - Otherwise:
        → Find up to 3 recent posts from the same category.
    - Excludes the current post from related list.

    Args:
        request (HttpRequest): The incoming request.
        slug (str): Slug of the news article.

    Returns:
        HttpResponse: Rendered "home/news_detail.html" with post and related_news context.
    """
    post = get_object_or_404(News, slug=slug, status="published")

    # Prefer related posts by tags (if any)
    if post.tags.exists():
        related_news = (
            News.objects.filter(status="published", tags__in=post.tags.all())
            .exclude(id=post.id)
            .distinct()  # prevent duplicates if multiple tags overlap
            .order_by("-created_at")[:3]
        )
    else:
        # Fallback: use category for related posts
        related_news = (
            News.objects.filter(status="published", category=post.category)
            .exclude(id=post.id)
            .order_by("-created_at")[:3]
        )

    return render(
        request,
        "home/news_detail.html",
        {"post": post, "related_news": related_news},
    )
