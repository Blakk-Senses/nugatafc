from django.urls import path
from dashboard.views import (
    news_create, news_delete,
    news_edit, news_manager, news_publish, standings_delete,
    standings_manager, manage_standings, standings_edit,
    analytics_dashboard, settings_general, settings_integrations, 
    settings_team, social_delete, menu_delete, edit_team_member,
    update_club_settings, update_menu_items, update_social_links,
    create_role, create_team_member, assign_cms_user, delete_team_member,
)
from matches.views import (
    team_manager, team_create, team_delete, team_edit,
    match_delete, match_edit, match_manager, manage_match, match_info,
)
from players.views import (
    player_create, player_manager, manage_player, manage_performance,
    delete_playerseason, player_edit, player_delete, 
    performance_list, performance_delete
)
from django.contrib.auth import views as auth_views

app_name = "dashboard"

urlpatterns = [

    path("news/create/", news_create, name="news_create"),
    path("news/", news_manager, name="news_manager"),
    path("news/<int:pk>/edit/", news_edit, name="news_edit"),
    path("news/<int:pk>/delete/", news_delete, name="news_delete"),
    path("news/<int:pk>/publish/", news_publish, name="news_publish"),

    # --- TEAMS ---
    path("teams/", team_manager, name="team_manager"),
    path("teams/create/", team_create, name="team_create"),
    path("teams/<int:pk>/edit/", team_edit, name="team_edit"),
    path("teams/<int:pk>/delete/", team_delete, name="team_delete"),

    # --- FIXTURES ---
    path("matches/", match_manager, name="match_manager"),
    path('matches/manage/', manage_match, name='manage_match'),
    path('matches/edit/<int:pk>/', match_edit, name='match_edit'),
    path('matches/delete/<int:pk>/', match_delete, name='match_delete'),
    path('match-info/<int:match_id>/', match_info, name='match_info'),


    # --- Player ---
    
    path("player-manager/", player_manager, name="player_manager"),  # All players
    path("player-manager/<int:season_id>/", player_manager, name="player_manager_by_season"),  # Filtered

    path("manage-player/", manage_player, name="manage_player"),
    path("manage-player/<int:playerseason_id>/", manage_player, name="manage_player_edit"),
    path("delete-playerseason/<int:pk>/", delete_playerseason, name="delete_playerseason"),

    path("performances/", performance_list, name="performance_list"),
    path('performances/add/', manage_performance, name='performance_add'),
    path('performances/edit/<int:match_id>/', manage_performance, name='performance_edit'),
    path('performances/delete/<int:match_id>/', performance_delete, name='performance_delete'),

    
    # Standings URLs
    path('standings/', standings_manager, name='standings_manager'),
    path('standings/manage/', manage_standings, name='manage_standings'),
    path('standings/edit/<int:pk>/', standings_edit, name='standings_edit'),
    path('standings/delete/<int:pk>/', standings_delete, name='standings_delete'),


    path("settings/general/", settings_general, name="settings_general"),
    path('settings/update-club-settings/', update_club_settings, name='update_club_settings'),
    path('settings/update-social-links/', update_social_links, name='update_social_links'),
    path('settings/update-menu-items/', update_menu_items, name='update_menu_items'),
    path("settings/social/delete/<int:pk>/", social_delete, name="social_delete"),
    path('settings/menu/delete/<int:pk>/', menu_delete, name='menu_delete'),


    path("settings/team/", settings_team, name="settings_team"),
    path("settings/team/create-role/", create_role, name="create_role"),
    path("settings/team/create-member/", create_team_member, name="create_team_member"),
    path("settings/team/assign-cms/", assign_cms_user, name="assign_cms_user"),
    path("settings/team/delete/<int:member_id>/", delete_team_member, name="delete_team_member"),
    path("settings/team/<int:member_id>/edit/", edit_team_member, name="edit_team_member"),
    path("settings/team/player/create/", player_create, name="player_create"),
    path("settings/team/player/<int:player_id>/edit/", player_edit, name="player_edit"),
    path("settings/team/player/<int:player_id>/delete/", player_delete, name="player_delete"),
    path("settings/integrations/", settings_integrations, name="settings_integrations"),
    
    

    path('analytics/', analytics_dashboard, name='analytics_dashboard'),
    path("login/", auth_views.LoginView.as_view(template_name="dashboard/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="dashboard:login"), name="logout"),

]
