from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from authors.models import Author
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.conf import settings

def author_list(request):
    authors = Author.objects.all()
    return render(request, "authors/authorList.html", {"authors": authors})

def author_create(request):
	return HttpResponse("author create (not implemented)")

def author_detail(request, author_serial):
    author = get_object_or_404(Author, serial=author_serial)
    return render(request, "authors/authorDetail.html", {"author": author})

@login_required
def author_edit(request, author_serial):
    author = Author.objects.get(serial=author_serial)

    if request.method == "POST":
        # Update text fields
        author.displayName = request.POST.get("displayName", author.displayName)
        author.description = request.POST.get("description", author.description)
        author.web = request.POST.get("web", author.web)
        author.github = request.POST.get("github", author.github)

        if "profileImageFile" in request.FILES:
            uploaded_file = request.FILES["profileImageFile"]
            # Save file in MEDIA_ROOT/profile_images/
            path = default_storage.save(f"profile_images/{uploaded_file.name}", uploaded_file)
            # Generate full URL
            author.profileImage = request.build_absolute_uri(f"{settings.MEDIA_URL}{path}")
        else:
            url_input = request.POST.get("profileImage", "").strip()
            if url_input:
                author.profileImage = url_input

        # Save changes
        author.save()

        return redirect("authors:detail", author_serial=author.serial)

    return render(request, "authors/authorEdit.html", {"author": author})

def author_entries_page(request, author_serial):
	return HttpResponse(f"author entries {author_serial} (not implemented)")

def author_followers_page(request, author_serial):
	return HttpResponse(f"author followers {author_serial} (not implemented)")

def follow_requests_page(request, author_serial):
	return HttpResponse(f"follow requests {author_serial} (not implemented)")
