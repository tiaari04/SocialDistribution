from django.http import HttpResponse
from django.shortcuts import get_object_or_404, get_list_or_404, render, redirect
from authors.models import Author
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.conf import settings
from inbox.models import FollowRequest
from entries.models import Entry

@login_required
def author_list(request):
    authors = Author.objects.all()
    return render(request, "authors/authorList.html", {"authors": authors})

def author_detail(request, author_serial):
    author = get_object_or_404(Author, serial=author_serial)
    is_following = False

    if request.user.is_authenticated:
        user_author = request.user.author
        is_following = FollowRequest.objects.filter(
            actor=user_author, 
            author_followed=author
            ).exists()
    entries = get_list_or_404(Entry, author_id=author.id)
    return render(request, "authors/authorDetail.html", {"author": author, "is_following": is_following, "entries": entries})

@login_required
def author_edit(request, author_serial):
    author = Author.objects.get(serial=author_serial)

    if request.method == "POST":
        # save updates
        author.displayName = request.POST.get("displayName", author.displayName)
        author.description = request.POST.get("description", author.description)
        author.web = request.POST.get("web", author.web)
        author.github = request.POST.get("github", author.github)

        if "profileImageFile" in request.FILES:
            uploaded_file = request.FILES["profileImageFile"]
            path = default_storage.save(f"profile_images/{uploaded_file.name}", uploaded_file)
            author.profileImage = request.build_absolute_uri(f"{settings.MEDIA_URL}{path}")
        else:
            url_input = request.POST.get("profileImage", "").strip()
            if url_input:
                author.profileImage = url_input

        # Save changes
        author.save()

        return redirect("authors:detail", author_serial=author.serial)

    return render(request, "authors/authorEdit.html", {"author": author})

@login_required
def author_entries_page(request, author_serial):
	return HttpResponse(f"author entries {author_serial} (not implemented)")

@login_required
def author_followers_page(request, author_serial):
	return HttpResponse(f"author followers {author_serial} (not implemented)")

@login_required
def follow_requests_page(request, author_serial):
	author = get_object_or_404(Author, serial=author_serial)

	requests = FollowRequest.objects.filter(author_followed=author, state=FollowRequest.State.REQUESTING).select_related('actor')

	context = {"author": author, "requests": requests}

	return render(request, "follow_requests.html", context)