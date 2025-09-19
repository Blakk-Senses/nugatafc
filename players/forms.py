from django import forms
from .models import Player, PlayerSeason, PlayerMatchPerformance
from django.forms import modelformset_factory



class PlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = [
            "first_name",
            "last_name",
            "slug",
            "date_of_birth",
            "joined_date",
            "bio",
            "photo",
            "height",
            "debut_date",
            "place_of_birth",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "slug": forms.TextInput(attrs={"class": "form-control", "placeholder": "Auto-generated if left blank"}),
            "date_of_birth": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "joined_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "height": forms.NumberInput(attrs={"min": 0, "step": 0.01, "class": "form-control", "placeholder": "in meters"}),
            "debut_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "place_of_birth": forms.TextInput(attrs={"class": "form-control"}),
        }



class PlayerSeasonForm(forms.ModelForm):
    class Meta:
        model = PlayerSeason
        fields = [
            "player",
            "season",
            "positions",
            "jersey_number",
        ]
        widgets = {
            "positions": forms.CheckboxSelectMultiple(),
            "jersey_number": forms.NumberInput(attrs={"min": 0, "class": "form-control"}),
        }


class PlayerMatchPerformanceForm(forms.ModelForm):
    class Meta:
        model = PlayerMatchPerformance
        fields = [
            "minutes_played",
            "goals",
            "assists",
            "clean_sheet",
            "big_chances_created",
            "tackles_won",
            "clearances",
            "penalties_taken",
            "penalties_scored",
            "penalties_saved",
            "saves",
            "yellow_cards",
            "red_cards",
        ]
        widgets = {
            "minutes_played": forms.NumberInput(attrs={"min": 0, "class": "stat-input"}),
            "goals": forms.NumberInput(attrs={"min": 0, "class": "stat-input"}),
            "assists": forms.NumberInput(attrs={"min": 0, "class": "stat-input"}),
            "clean_sheet": forms.CheckboxInput(attrs={"class": "stat-checkbox"}),
            "big_chances_created": forms.NumberInput(attrs={"min": 0, "class": "stat-input"}),
            "tackles_won": forms.NumberInput(attrs={"min": 0, "class": "stat-input"}),
            "clearances": forms.NumberInput(attrs={"min": 0, "class": "stat-input"}),
            "penalties_taken": forms.NumberInput(attrs={"min": 0, "class": "stat-input"}),
            "penalties_scored": forms.NumberInput(attrs={"min": 0, "class": "stat-input"}),
            "penalties_saved": forms.NumberInput(attrs={"min": 0, "class": "stat-input"}),
            "saves": forms.NumberInput(attrs={"min": 0, "class": "stat-input"}),
            "yellow_cards": forms.NumberInput(attrs={"min": 0, "class": "stat-input"}),
            "red_cards": forms.NumberInput(attrs={"min": 0, "class": "stat-input"}),
        }



# 🔥 Formset for bulk editing
PlayerMatchPerformanceFormSet = modelformset_factory(
    PlayerMatchPerformance,
    form=PlayerMatchPerformanceForm,
    extra=0,          # no empty rows
    can_delete=False  # don't allow deleting via bulk entry
)
