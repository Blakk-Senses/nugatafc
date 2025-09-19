from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import os
from .models import Player, PlayerMatchPerformance
from django.db import models



@receiver([post_save, post_delete], sender=PlayerMatchPerformance)
def update_player_season_totals(sender, instance, **kwargs):
    season = instance.player_season
    agg = season.performances.aggregate(
        appearances=models.Count("id"),
        goals=models.Sum("goals"),
        assists=models.Sum("assists"),
        clean_sheets=models.Sum(
            models.Case(
                models.When(clean_sheet=True, then=1),
                default=0,
                output_field=models.IntegerField()
            )
        ),
        big_chances_created=models.Sum("big_chances_created"),
        tackles_won=models.Sum("tackles_won"),
        clearances=models.Sum("clearances"),
        penalties_taken=models.Sum("penalties_taken"),
        penalties_scored=models.Sum("penalties_scored"),
        penalties_saved=models.Sum("penalties_saved"),
        saves=models.Sum("saves"),
        yellow_cards=models.Sum("yellow_cards"),
        red_cards=models.Sum("red_cards"),
    )
    for field, value in agg.items():
        setattr(season, field, value or 0)
    season.save(update_fields=agg.keys())
