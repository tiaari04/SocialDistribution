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
from django.urls import reverse

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.urls import reverse
from authors.models import Author

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            try:
                author = Author.objects.get(user=user)
                if author.is_approved:
                    return redirect(reverse("entries:stream_home", kwargs={"author_serial": author.serial}))
                else:
                    return render(request, "login/login.html", {"error": "Your account is pending approval."})
            except Author.DoesNotExist:
                return render(request, "login/login.html", {"error": "Author not found"})
        else:
            return render(request, "login/login.html", {"error": "Invalid username or password"})

    return render(request, "login/login.html")


def signup_view(request):
    if request.method == "POST":
        form = CustomSignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()

            # Get current site domain
            current_site = Site.objects.get_current()

            domain = f"https://{current_site.domain}" 

            profile_url = ""
            # Handle profile image upload
            uploaded_file = form.cleaned_data.get("profileImageFile")
            if "profileImageFile" in request.FILES:
                uploaded_file = request.FILES["profileImageFile"]
                path = default_storage.save(f"profile_images/{uploaded_file.name}", uploaded_file)
                profile_url = request.build_absolute_uri(f"{settings.MEDIA_URL}{path}")
            else:
      
                url_input = request.POST.get("profileImage", "").strip()
                if url_input:
                    profile_url = url_input

            # Create Author instance with full URL
            author = Author.objects.create(
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
            return redirect(reverse("entries:stream_home", kwargs={"author_serial": author.serial}))

    else:
        form = CustomSignupForm()

    return render(request, "login/signup.html", {"form": form})
