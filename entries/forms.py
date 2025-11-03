from django import forms
from .models import Entry

class EntryForm(forms.ModelForm):
    image_file = forms.FileField(required=False,widget=forms.ClearableFileInput(attrs={"class": "form-control-file"}))

    class Meta:
        model = Entry
        fields = ["title", "description", "content", "image_file", "content_type", "visibility"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter a title"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Short description"}),
            "content": forms.Textarea(attrs={"class": "form-control", "rows": 5, "placeholder": "Write your post..."}),
            "content_type": forms.Select(attrs={"class": "form-control"}),
            "visibility": forms.Select(attrs={"class": "form-control"}),
        }
