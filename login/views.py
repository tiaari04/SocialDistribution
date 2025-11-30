from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.core.files.storage import default_storage
from django.conf import settings
from .forms import CustomSignupForm
from django.utils.crypto import get_random_string
from django.contrib.sites.models import Site
from django.urls import reverse
from django.contrib.sites.models import Site
from .forms import CustomSignupForm
from django.utils.crypto import get_random_string

from authors.models import Author
from federation.models import FederatedNode
from adminpage.models import HostedImage

import os
import uuid

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            try:
                author = Author.objects.get(user=user)
                if author.is_admin:
                    return redirect(reverse("adminpage:dashboard"))
                if author.is_approved and author.is_active:
                    return redirect(reverse("entries:stream_home", kwargs={"author_serial": author.serial}))
                # Account not approved yet 
                return redirect("login:await_approval")
            except Author.DoesNotExist:
                # Author record missing
                return redirect("login:login")
        else:
            # Invalid credentials
            return redirect("login:login")

    return render(request, "login/login.html")



def signup_view(request):
    if request.method == "POST":
        form = CustomSignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()

            current_site = Site.objects.get_current()

            domain = ''
            try:
                local_node = FederatedNode.objects.get(is_local=True)
                domain = local_node.base_url.rstrip('/')
            except Exception as e:
                print("Error getting domain: ", e)

            profile_url = ""
            uploaded_file = form.cleaned_data.get("profileImageFile")
            if "profileImageFile" in request.FILES:
                uploaded_file = request.FILES["profileImageFile"]
                # Save the uploaded profile image as a HostedImage 
                hosted = HostedImage(file=uploaded_file, uploaded_by=user)
                hosted.save()
                profile_url = request.build_absolute_uri(hosted.file.url)
            else:
                profile_url = "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_640.png"

            # Create Author instance
            serial = str(uuid.uuid4())
            author = Author.objects.create(
                id=f"{domain}/api/authors/{serial}",
                user=user,
                host=f"{domain}/api/",
                displayName=user.username,
                github=form.cleaned_data.get('githubLink', ''),
                profileImage=profile_url,  
                web=form.cleaned_data.get('web', ''),
                description=form.cleaned_data.get('description', ''),
                is_local=True,
                serial=serial,
            )

            # do not log in until validated
            #login(request, user)
            return render(request, "login/awaitApproval.html")

    else:
        form = CustomSignupForm()

    return render(request, "login/signup.html", {"form": form})

def await_approval_view(request):
    return render(request, "login/awaitApproval.html")
