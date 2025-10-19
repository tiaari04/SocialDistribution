# login/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.core.files.storage import default_storage
from django.conf import settings
from django.contrib.auth.models import User
from .forms import CustomSignupForm
from authors.models import Author
from django.utils.crypto import get_random_string
from django.contrib.sites.models import Site

from django.utils.text import slugify
import os

def signup_view(request):
    if request.method == "POST":
        form = CustomSignupForm(request.POST, request.FILES)
        if form.is_valid():
            # Create the user
            user = form.save()
            current_site = Site.objects.get_current()
            domain = f"https://{current_site.domain}"

            # Handle profile image upload
            uploaded_file = form.cleaned_data.get("profileImageFile")
            profile_url = ""
            if uploaded_file:
                # Use slugified filename + random string to avoid overwriting
                base, ext = os.path.splitext(uploaded_file.name)
                filename = f"{slugify(user.username)}_{get_random_string(8)}{ext}"
                path = default_storage.save(f"profile_images/{filename}", uploaded_file)
                profile_url = f"{settings.MEDIA_URL}{path}"  # URL to store in DB

            # Create Author instance
            Author.objects.create(
                id=f"{domain}/authors/{user.username}",
                host=f"{domain}/api/",
                displayName=user.username,
                github=form.cleaned_data.get('githubLink', ''),
                profileImage=profile_url,  
                web=form.cleaned_data.get('web', ''),
                description=form.cleaned_data.get('description', ''),
                is_local=True,
                serial=get_random_string(12),
            )

            # Log the user in
            login(request, user)
            return redirect('/authors/')
    else:
        form = CustomSignupForm()

    return render(request, "login/signup.html", {"form": form})
