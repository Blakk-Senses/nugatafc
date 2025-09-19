from django import forms
from .models import News
from django_ckeditor_5.widgets import CKEditor5Widget
from taggit.forms import TagField


class NewsCoreForm(forms.ModelForm):
    tags = TagField(
        required=False,
        help_text="Add tags separated by commas",
        widget=forms.TextInput(
            attrs={
                "id": "id_core-tags",
                "class": "form-control",
                "data-placeholder": "Add tags...",
                "autocomplete": "off",
            }
        )
    )

    class Meta:
        model = News
        fields = ["title", "slug", "excerpt", "content", "category", "cover_image", "tags"]
        widgets = {
            "content": CKEditor5Widget(config_name="default"),
            "excerpt": forms.Textarea(attrs={"rows": 3}),
            "cover_image": forms.ClearableFileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Fix tags display for existing instances
        if self.instance and self.instance.pk:
            tags = self.instance.tags.all()
            self.fields['tags'].initial = ', '.join([tag.name for tag in tags])


class NewsSEOForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ["seo_title", "seo_description", "seo_keywords"]
        widgets = {
            "seo_description": forms.Textarea(attrs={"rows": 2, "placeholder": "Meta description for search engines..."}),
            "seo_keywords": forms.TextInput(attrs={"placeholder": "Comma-separated keywords"}),
        }


class NewsSocialForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ["og_image"]


class NewsSettingsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ["allow_comments"]
        widgets = {
            "allow_comments": forms.CheckboxInput(),
        }
