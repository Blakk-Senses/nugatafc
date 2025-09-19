import datetime
from django.core.management.base import BaseCommand
from dashboard.models import Season

class Command(BaseCommand):
    help = "Seed Season data from 2024/25 up to 2100/01"

    def handle(self, *args, **kwargs):
        start_year = 2024
        end_year = 2100

        created_count = 0
        for year in range(start_year, end_year + 1):
            name = f"{year}/{year+1}"
            start_date = datetime.date(year, 8, 1)
            end_date = datetime.date(year + 1, 6, 30)  

            season, created = Season.objects.get_or_create(
                name=name,
                defaults={"start_date": start_date, "end_date": end_date}
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {created_count} new seasons."))
