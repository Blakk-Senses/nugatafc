from django.core.management.base import BaseCommand
from django.db import transaction
from matches.models import Match, Standing  # Replace 'your_app' with your actual app name

class Command(BaseCommand):
    help = 'Update all standings based on completed matches'

    def add_arguments(self, parser):
        parser.add_argument(
            '--season',
            help='Specific season to update (e.g., "2024/2025")',
        )
        parser.add_argument(
            '--match-type',
            help='Specific match type to update (e.g., "division_two")',
        )

    def handle(self, *args, **options):
        season = options['season']
        match_type = options['match_type']
        
        # Build query based on provided options
        match_filters = {'status': 'finished'}
        if season:
            match_filters['season'] = season
        if match_type:
            match_filters['match_type'] = match_type
            
        # Get finished matches based on filters
        finished_matches = Match.objects.filter(**match_filters)
        
        if not finished_matches.exists():
            self.stdout.write(self.style.WARNING('No finished matches found to process.'))
            return
        
        self.stdout.write(f'Processing {finished_matches.count()} finished matches...')
        
        # Use transaction to ensure data consistency
        with transaction.atomic():
            # Reset relevant standings to zero
            standing_filters = {}
            if season:
                standing_filters['season'] = season
            if match_type:
                standing_filters['match_type'] = match_type
                
            if standing_filters:  # Only reset filtered standings
                Standing.objects.filter(**standing_filters).update(
                    played=0, won=0, drawn=0, lost=0,
                    goal_for=0, goal_against=0, points=0, goal_difference=0
                )
            else:  # Reset all standings if no filters
                Standing.objects.all().update(
                    played=0, won=0, drawn=0, lost=0,
                    goal_for=0, goal_against=0, points=0, goal_difference=0
                )
            
            # Process all finished matches
            count = 0
            for match in finished_matches:
                self.update_standings_from_match(match)
                count += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated standings from {count} matches')
            )
    
    def update_standings_from_match(self, match):
        """Update standings based on a single match"""
        # Get or create standing for home team
        home_standing, created = Standing.objects.get_or_create(
            team=match.home_team,
            match_type=match.match_type,
            season=match.season,
            defaults={
                'played': 0, 'won': 0, 'drawn': 0, 'lost': 0,
                'goal_for': 0, 'goal_against': 0
            }
        )
        
        # Get or create standing for away team
        away_standing, created = Standing.objects.get_or_create(
            team=match.away_team,
            match_type=match.match_type,
            season=match.season,
            defaults={
                'played': 0, 'won': 0, 'drawn': 0, 'lost': 0,
                'goal_for': 0, 'goal_against': 0
            }
        )
        
        # Update matches played
        home_standing.played += 1
        away_standing.played += 1
        
        # Update goals
        home_standing.goal_for += match.home_score
        home_standing.goal_against += match.away_score
        away_standing.goal_for += match.away_score
        away_standing.goal_against += match.home_score
        
        # Update results
        if match.home_score > match.away_score:
            home_standing.won += 1
            away_standing.lost += 1
        elif match.home_score < match.away_score:
            home_standing.lost += 1
            away_standing.won += 1
        else:
            home_standing.drawn += 1
            away_standing.drawn += 1
        
        # Save both standings (this will automatically calculate points and GD)
        home_standing.save()
        away_standing.save()