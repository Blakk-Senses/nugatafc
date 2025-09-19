
from django.db import models
from dashboard.models import Season, get_current_season
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver



class Position(models.Model):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


from django.utils.text import slugify

class Player(models.Model):
    first_name = models.CharField(max_length=50, default="Blakk")
    last_name = models.CharField(max_length=50, default="Senses")
    slug = models.SlugField(unique=True, blank=True)

    date_of_birth = models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='player_photos/', blank=True, null=True)
    joined_date = models.DateField(blank=True, null=True)

    # Moved fields here
    height = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)  # meters
    debut_date = models.DateField(blank=True, null=True)
    place_of_birth = models.CharField(max_length=100, blank=True, null=True)

    seasons = models.ManyToManyField(Season, through="PlayerSeason")

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.full_name)
            slug = base_slug
            counter = 1
            while Player.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)



MATCH_TYPE_CHOICES = [
    ("division_two", "Division Two League"),
    ("sub_middle", "Sub Middle League"),
    ("middle", "Middle League"),
    ("fa_cup", "FA Cup"),
    ("friendlies", "Club Friendlies"),
]

class PlayerSeason(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    season = models.ForeignKey(
        Season,
        on_delete=models.CASCADE,
        related_name="player_seasons",
        default=get_current_season,
    )
    positions = models.ManyToManyField(Position, blank=True) 
    jersey_number = models.PositiveIntegerField()

    # Performance stats (aggregates across match types)
    appearances = models.PositiveIntegerField(default=0)  
    goals = models.PositiveIntegerField(default=0)  
    assists = models.PositiveIntegerField(default=0)  
    clean_sheets = models.PositiveIntegerField(default=0)
    big_chances_created = models.PositiveIntegerField(default=0)  
    tackles_won = models.PositiveIntegerField(default=0)  
    clearances = models.PositiveIntegerField(default=0)  
    penalties_saved = models.PositiveIntegerField(default=0)  
    penalties_scored = models.PositiveIntegerField(default=0)  
    saves = models.PositiveIntegerField(default=0)  
    yellow_cards = models.PositiveIntegerField(default=0)
    red_cards = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("player", "season")

    def __str__(self):
        positions = ", ".join(p.code for p in self.positions.all()) or "No Position"
        return f"{self.player.full_name} ({positions}) - {self.season.name}"


class PlayerMatchPerformance(models.Model):
    player_season = models.ForeignKey(
        PlayerSeason,
        on_delete=models.CASCADE,
        related_name="performances"
    )
    match = models.ForeignKey(
        "matches.Match",
        on_delete=models.CASCADE,
        related_name="player_performances"
    )

    # 📌 Match type
    match_type = models.CharField(
        max_length=20,
        choices=MATCH_TYPE_CHOICES,
        default="division_two"
    )

    # Match-specific stats
    minutes_played = models.PositiveIntegerField(default=0)
    goals = models.PositiveIntegerField(default=0)
    assists = models.PositiveIntegerField(default=0)
    clean_sheet = models.BooleanField(default=False)
    big_chances_created = models.PositiveIntegerField(default=0)
    tackles_won = models.PositiveIntegerField(default=0)
    clearances = models.PositiveIntegerField(default=0)
    penalties_taken = models.PositiveIntegerField(default=0)
    penalties_scored = models.PositiveIntegerField(default=0)
    penalties_saved = models.PositiveIntegerField(default=0)
    saves = models.PositiveIntegerField(default=0)
    yellow_cards = models.PositiveIntegerField(default=0)
    red_cards = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("player_season", "match")

    def __str__(self):
        return f"{self.player_season.player.full_name} - {self.match}"
