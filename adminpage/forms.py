from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import HostedImage
from authors.models import Author  # <- your Author

User = get_user_model()

class HostedImageForm(forms.ModelForm):
    class Meta:
        model = HostedImage
        fields = ['file', 'alt_text', 'is_public']

class AuthorForm(forms.ModelForm):
    """
    Form for your Author model with URL PK.
    Note: 'id' is the Author FQID; for local authors we'll usually generate it.
    """
    class Meta:
        model = Author
        fields = [
            'id',   
            'user',
            'host',
            'displayName',
            'github',
            'profileImage',
            'web',
            'description',
            'is_local',
            'is_admin',
            'is_active',
            'serial',
        ]
        widgets = {
            'id': forms.URLInput(attrs={'placeholder': 'https://your-node/api/authors/<uuid>'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
