from django.db import models
from dashboard.models import get_current_season


# ============================
# Team Model
# ============================
class Team(models.Model):
    name = models.CharField(max_length=100)
    stadium = models.CharField(max_length=100, blank=True)
    logo = models.ImageField(upload_to='team_logos/', blank=True, null=True)

    # 🔥 Reference Season by app_label.ModelName (no direct import!)
    season = models.ForeignKey(
        'dashboard.Season',
        on_delete=models.CASCADE,
        related_name="teams",
        default=get_current_season,
    )

    def __str__(self):
        return f"{self.name}"


# ============================
# Match Model
# ============================
class Match(models.Model):
    STATUS_CHOICES = [
        ("upcoming", "Upcoming"),
        ("finished", "Finished"),
    ]

    MATCH_TYPE_CHOICES = [
        ("division_two", "Division Two League"),
        ("sub_middle", "Sub Middle League"),
        ("middle", "Middle League"),
        ("fa_cup", "FA Cup"),
        ("friendlies", "Club Friendlies"),
    ]

    home_team = models.ForeignKey(Team, related_name="home_matches", on_delete=models.CASCADE)
    away_team = models.ForeignKey(Team, related_name="away_matches", on_delete=models.CASCADE)
    date = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    home_score = models.PositiveIntegerField(null=True, blank=True)
    away_score = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="upcoming")
    match_type = models.CharField(max_length=50, choices=MATCH_TYPE_CHOICES, default="division_two")

    # 🔥 Reference Season as string
    season = models.ForeignKey(
        'dashboard.Season',
        on_delete=models.CASCADE,
        related_name="matches",
        default=get_current_season,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.home_team} vs {self.away_team}"

    @property
    def is_finished(self):
        return self.status == "finished"


# ============================
# Standing Model
# ============================
class Standing(models.Model):
    MATCH_TYPE_CHOICES = [
        ("division_two", "Division Two League"),
        ("sub_middle", "Sub Middle League"),
        ("middle", "Middle League"),
        ("fa_cup", "FA Cup"),
        ("friendlies", "Club Friendlies"),
    ]

    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    played = models.PositiveIntegerField(default=0)
    won = models.PositiveIntegerField(default=0)
    drawn = models.PositiveIntegerField(default=0)
    lost = models.PositiveIntegerField(default=0)
    goal_for = models.PositiveIntegerField(default=0)
    goal_against = models.PositiveIntegerField(default=0)

    # Calculated fields
    goal_difference = models.IntegerField(default=0)
    points = models.PositiveIntegerField(default=0)

    match_type = models.CharField(max_length=50, choices=MATCH_TYPE_CHOICES, default="division_two")

    # 🔥 Reference Season as string
    season = models.ForeignKey(
        'dashboard.Season',
        on_delete=models.CASCADE,
        related_name="standings",
        default=get_current_season,
    )

    class Meta:
        unique_together = ("team", "match_type", "season")  # one standing per team per league & season

    def __str__(self):
        return f"{self.team.name} ({self.match_type} - {self.season})"

    def save(self, *args, **kwargs):
        # Calculate points and goal difference before saving
        self.points = self.won * 3 + self.drawn
        self.goal_difference = self.goal_for - self.goal_against
        super().save(*args, **kwargs)
