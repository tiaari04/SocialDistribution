from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.core.files.storage import default_storage
from django.conf import settings
from django.contrib.auth.models import User
from .forms import CustomSignupForm
from authors.models import Author
from django.utils.crypto import get_random_string
from django.contrib.sites.models import Site
import os
from django.utils.text import slugify

def signup_view(request):
    if request.method == "POST":
        form = CustomSignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()

            # Get current site domain
            current_site = Site.objects.get_current()
            domain = f"https://{current_site.domain}"  # full domain
            profile_url = ""
            # Handle profile image upload
            uploaded_file = form.cleaned_data.get("profileImageFile")
            if "profileImageFile" in request.FILES:
                uploaded_file = request.FILES["profileImageFile"]
                # Save file in MEDIA_ROOT/profile_images/
                path = default_storage.save(f"profile_images/{uploaded_file.name}", uploaded_file)
                # Generate full URL
                profile_url = request.build_absolute_uri(f"{settings.MEDIA_URL}{path}")
            else:
                # 2️⃣ Fallback: use URL field if provided
                url_input = request.POST.get("profileImage", "").strip()
                if url_input:
                    profile_url = url_input

            # Create Author instance with full URL
            Author.objects.create(
                id=f"{domain}/authors/{user.username}",
                user=user,
                host=f"{domain}/api/",
                displayName=user.username,
                github=form.cleaned_data.get('githubLink', ''),
                profileImage=profile_url,  
                web=form.cleaned_data.get('web', ''),
                description=form.cleaned_data.get('description', ''),
                is_local=True,
                serial=get_random_string(12),
            )

            login(request, user)
            return redirect('/authors/')
    else:
        form = CustomSignupForm()

    return render(request, "login/signup.html", {"form": form})
