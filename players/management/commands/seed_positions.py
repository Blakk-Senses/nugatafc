from django.core.management.base import BaseCommand
from players.models import Position   # ✅ your app name here

class Command(BaseCommand):
    help = "Seed the database with default football positions"

    def handle(self, *args, **kwargs):
        positions = [
            ("GK", "Goalkeeper"),
            ("RB", "Right Back"),
            ("LB", "Left Back"),
            ("CB", "Centre Back"),
            ("DM", "Defensive Midfielder"),
            ("CM", "Central Midfielder"),
            ("AM", "Attacking Midfielder"),
            ("WG", "Winger"),
            ("FW", "Forward"),
            ("ST", "Striker"),
        ]

        for code, name in positions:
            obj, created = Position.objects.get_or_create(code=code, defaults={"name": name})
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Added {name}"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ {name} already exists"))
