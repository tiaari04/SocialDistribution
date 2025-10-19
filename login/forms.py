# login/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomSignupForm(UserCreationForm):
    githubLink = forms.URLField(required=False, label="GitHub Profile URL")
    profileImageFile = forms.ImageField(required=False, label="Profile Image")
    web = forms.URLField(required=False, label="Website")
    description = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = User
        fields = ("username", "profileImageFile", "password1", "password2", "githubLink",  "web", "description")
