from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Project, ProjectImage, Comment, Donation, Rating, Report


class ProjectForm(forms.ModelForm):
    """Create / edit a project campaign."""

    class Meta:
        model = Project
        fields = [
            "title", "details", "category", "tags",
            "total_target", "start_date", "end_date",
        ]
        widgets = {
            "details": forms.Textarea(attrs={"rows": 6}),
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["total_target"].disabled = True
            self.fields["total_target"].help_text = "Target amount cannot be changed after project creation."

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date:
            # Only validate start_date not being in the past when creating new project
            if not (self.instance and self.instance.pk) and start_date < timezone.localdate():
                raise ValidationError("Start date cannot be in the past.")
            if end_date <= start_date:
                raise ValidationError("End date must be after the start date.")

        total_target = cleaned_data.get("total_target")
        if total_target is not None and total_target <= 0:
            raise ValidationError("Total target must be greater than zero.")

        return cleaned_data


# Multiple image upload support: a small custom widget/field pair.
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return single_file_clean(data, initial)


class ProjectImageUploadForm(forms.Form):
    images = MultipleFileField(required=False)


class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = ["amount"]

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise ValidationError("Donation amount must be greater than zero.")
        return amount


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 3, "placeholder": "Write a comment..."}),
        }


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ["stars"]
        widgets = {
            "stars": forms.HiddenInput(),  # populated by JS star-rating widget
        }


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["reason", "details"]
        widgets = {
            "details": forms.Textarea(attrs={"rows": 3, "placeholder": "Optional details..."}),
        }
