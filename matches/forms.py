from django import forms
from .models import Match, Standing, Team
from dashboard.models import Season, get_current_season


# ============================
# Utility: Update standings
# ============================
def update_standings_from_match(match):
    if match.status != 'finished':
        return
    
    home_standing, _ = Standing.objects.get_or_create(
        team=match.home_team,
        match_type=match.match_type,
        season=match.season,
        defaults={"played": 0, "won": 0, "drawn": 0, "lost": 0, "goal_for": 0, "goal_against": 0}
    )

    away_standing, _ = Standing.objects.get_or_create(
        team=match.away_team,
        match_type=match.match_type,
        season=match.season,
        defaults={"played": 0, "won": 0, "drawn": 0, "lost": 0, "goal_for": 0, "goal_against": 0}
    )

    home_standing.played += 1
    away_standing.played += 1

    home_standing.goal_for += match.home_score
    home_standing.goal_against += match.away_score
    away_standing.goal_for += match.away_score
    away_standing.goal_against += match.home_score

    if match.home_score > match.away_score:
        home_standing.won += 1
        away_standing.lost += 1
    elif match.home_score < match.away_score:
        home_standing.lost += 1
        away_standing.won += 1
    else:
        home_standing.drawn += 1
        away_standing.drawn += 1

    home_standing.save()
    away_standing.save()


# ============================
# Match Form
# ============================
class MatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ["home_team", "away_team", "date", "location", "match_type", "season"]
        widgets = {
            "date": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-input"}),
            "home_team": forms.Select(attrs={"class": "form-select"}),
            "away_team": forms.Select(attrs={"class": "form-select"}),
            "location": forms.TextInput(attrs={"class": "form-input"}),
            "match_type": forms.Select(attrs={"class": "form-select"}),
            "season": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.fields["season"].initial = get_current_season()
        except Exception:
            pass  # fallback if no season is found

    def save(self, commit=True):
        match = super().save(commit=False)
        match.status = "upcoming"
        if not match.location and match.home_team:
            match.location = match.home_team.stadium
        if commit:
            match.save()
        return match


# ============================
# Match Result Form
# ============================
class MatchResultForm(forms.ModelForm):
    match_selector = forms.ModelChoiceField(
        queryset=Match.objects.filter(status="upcoming").order_by("-date"),
        required=True,
        label="Select Match",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_match_selector'})
    )

    match_id = forms.IntegerField(required=True, widget=forms.HiddenInput(attrs={'id': 'id_match_id'}))

    class Meta:
        model = Match
        fields = ["home_score", "away_score"]
        widgets = {
            "home_score": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
            "away_score": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("match_selector"):
            cleaned_data["match_id"] = cleaned_data["match_selector"].id
            try:
                match = Match.objects.get(id=cleaned_data["match_selector"].id)
                if match.status != "upcoming":
                    self.add_error("match_selector", "Cannot add results to a completed match")
            except Match.DoesNotExist:
                self.add_error("match_selector", "Selected match does not exist")
        return cleaned_data

    def save(self, commit=True):
        match = Match.objects.get(id=self.cleaned_data["match_id"])
        match.home_score = self.cleaned_data["home_score"]
        match.away_score = self.cleaned_data["away_score"]
        match.status = "finished"

        if commit:
            match.save()
            update_standings_from_match(match)

        return match


# ============================
# Standing Form
# ============================
class StandingForm(forms.ModelForm):
    class Meta:
        model = Standing
        fields = ["team", "match_type", "season", "won", "drawn", "lost", "goal_for", "goal_against"]
        widgets = {
            "team": forms.Select(attrs={"class": "form-select"}),
            "match_type": forms.Select(attrs={"class": "form-select"}),
            "season": forms.Select(attrs={"class": "form-select"}),
            "won": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
            "drawn": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
            "lost": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
            "goal_for": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
            "goal_against": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.fields["season"].initial = get_current_season()
        except Exception:
            pass


# ============================
# Team Form
# ============================
class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["name", "logo", "stadium", "season"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input"}),
            "logo": forms.ClearableFileInput(attrs={"class": "form-input"}),
            "stadium": forms.TextInput(attrs={"class": "form-input"}),
            "season": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.fields["season"].initial = get_current_season()
        except Exception:
            pass
