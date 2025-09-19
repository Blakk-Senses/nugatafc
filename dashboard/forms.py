from django import forms
from .models import ClubGeneralSettings, ClubTeamMember, ClubRole, ClubIntegrationSettings
from django.contrib.auth.models import User
from django.forms import inlineformset_factory
from .models import ClubGeneralSettings, MenuItem, SocialLink


class ClubGeneralSettingsForm(forms.ModelForm):
    class Meta:
        model = ClubGeneralSettings
        fields = "__all__"
        widgets = {
            "primary_color": forms.TextInput(attrs={"type": "color"}),
            "secondary_color": forms.TextInput(attrs={"type": "color"}),
            "neutral_dark": forms.TextInput(attrs={"type": "color"}),
            "neutral_light": forms.TextInput(attrs={"type": "color"}),
            "meta_description": forms.Textarea(attrs={"rows": 3}),
        }


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ["label", "url_name", "external_url", "order"]
        widgets = {
            "order": forms.NumberInput(attrs={"min": 0}),
        }


class SocialLinkForm(forms.ModelForm):
    class Meta:
        model = SocialLink
        fields = ["platform", "url"]


MenuItemFormSet = inlineformset_factory(
    ClubGeneralSettings,
    MenuItem,
    form=MenuItemForm,
    extra=0,           
    can_delete=True
)

SocialLinkFormSet = inlineformset_factory(
    ClubGeneralSettings,
    SocialLink,
    form=SocialLinkForm,
    extra=0,           
    can_delete=True
)



class GroupedModelChoiceField(forms.ModelChoiceField):
    """Custom field that supports optgroups for categories."""

    def __init__(self, *args, **kwargs):
        self.group_by_field = kwargs.pop("group_by_field", None)
        super().__init__(*args, **kwargs)

    def _get_choices(self):
        if self.group_by_field:
            grouped_choices = {}
            for role in self.queryset:
                group_name = getattr(role, self.group_by_field)
                grouped_choices.setdefault(group_name, []).append((role.id, str(role)))

            choices = []
            for group, items in grouped_choices.items():
                choices.append((group.title(), items))
            return choices
        return super()._get_choices()

    choices = property(_get_choices)



class ClubRoleForm(forms.ModelForm):
    class Meta:
        model = ClubRole
        fields = ["name", "category"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-control"}),
        }


from django import forms
from .models import ClubTeamMember

class ClubTeamMemberForm(forms.ModelForm):
    class Meta:
        model = ClubTeamMember
        fields = [
            "picture",
            "first_name",
            "last_name",
            "date_of_birth",
            "role",
            "date_joined",
            "date_left",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "date_joined": forms.DateInput(attrs={"type": "date"}),
            "date_left": forms.DateInput(attrs={"type": "date"}),
            "role": forms.Select(attrs={"class": "form-control"}),
        }


class AssignCMSUserForm(forms.Form):
    member = forms.ModelChoiceField(
        queryset=ClubTeamMember.objects.filter(user_account__isnull=True),
        label="Team Member",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))

    def save(self):
        member = self.cleaned_data["member"]
        user = User.objects.create_user(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password"],
        )
        user.is_staff = True
        user.save()

        member.user_account = user
        member.save()
        return member




class ClubIntegrationSettingsForm(forms.ModelForm):
    class Meta:
        model = ClubIntegrationSettings
        fields = "__all__"
