from django.forms import model_to_dict
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse, HttpResponseForbidden
from adminpage.models import HostedImage
from inbox.models import FollowRequest
from .models import Entry
from authors.models import Author
from django.shortcuts import render, redirect, get_object_or_404
from .forms import EntryForm
from django.utils import timezone
import uuid
from django.contrib.auth.decorators import login_required

def stream_home(request, author_serial):
    current_author = get_object_or_404(Author, serial=author_serial)


    following = FollowRequest.objects.filter(
        actor=current_author, state=FollowRequest.State.ACCEPTED
    ).values_list("author_followed_id", flat=True)

    followers = FollowRequest.objects.filter(
        author_followed=current_author, state=FollowRequest.State.ACCEPTED
    ).values_list("actor_id", flat=True)

    friends = set(following).intersection(followers)


    base_entries = Entry.objects.exclude(visibility=Entry.Visibility.DELETED)


    public_entries = base_entries.filter(visibility=Entry.Visibility.PUBLIC)
    unlisted_entries = base_entries.filter(
        visibility=Entry.Visibility.UNLISTED,
        author_id__in=followers
    )
    friends_entries = base_entries.filter(
        visibility=Entry.Visibility.FRIENDS,
        author_id__in=friends
    )
    own_entries = base_entries.filter(author=current_author)

    entries = (
        public_entries
        | unlisted_entries
        | friends_entries
        | own_entries
    ).select_related("author").order_by("-published")

    return render(request, "stream_home.html", {
        "entries": entries,
        "author": current_author,
    })

def public_entries(request):
    """
    Returns all public entries.
    """
    if request.method == "GET":
        entries = Entry.objects.filter(visibility=Entry.Visibility.PUBLIC).order_by("-published")
        data = [model_to_dict(e) for e in entries]
        return JsonResponse(data, safe=False)
    return HttpResponseNotAllowed(["GET"])

@login_required
def entry_create(request, author_serial):
    author = get_object_or_404(Author, serial=author_serial)

    if request.method == "POST":
        form = EntryForm(request.POST, request.FILES or None)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.author = author

            # Assign a unique serial
            entry.serial = uuid.uuid4().hex[:12]

            # Generate fqid based on current host
            scheme = 'https' if request.is_secure() else 'http'
            domain = request.get_host()
            entry.fqid = f"{scheme}://{domain}/authors/{author.serial}/entries/{entry.serial}"

            # Handle image upload if present
            if 'image_file' in request.FILES:
                uploaded_file = request.FILES['image_file']
                hosted = HostedImage(file=uploaded_file, uploaded_by=request.user)
                hosted.save()
                entry.image_url = request.build_absolute_uri(hosted.file.url)

            entry.published = timezone.now()
            entry.save()
            return redirect("entries:stream_home", author_serial=author.serial)
    else:
        form = EntryForm()

    return render(request, "entries/entry_form.html", {"form": form, "author": author})


def entry_detail(request, author_serial, entry_serial):

    author = get_object_or_404(Author, serial=author_serial)
    entry = get_object_or_404(Entry, author=author, serial=entry_serial)

    # no one can see deleted posts
    if entry.visibility == Entry.Visibility.DELETED:
        return HttpResponseForbidden("This post has been deleted.")

    # everyone can see public posts
    if entry.visibility == Entry.Visibility.PUBLIC:
        return render(request, "stream_home.html", {"entries": [entry], "author": author})
    
    # if you have the link you can see unlisted posts
    if entry.visibility == Entry.Visibility.UNLISTED:
        return render(request, "stream_home.html", {"entries": [entry], "author": author})

    # you can always see your own posts

    if request.user.is_authenticated:
        viewer = request.user.author
        if viewer == author:
            return render(request, "stream_home.html", {"entries": [entry], "author": author})

        follows = FollowRequest.objects.filter(actor=viewer, author_followed=author, state=FollowRequest.State.ACCEPTED).exists()
        followed_by = FollowRequest.objects.filter(actor=author, author_followed=viewer, state=FollowRequest.State.ACCEPTED).exists()

        # friends can see friends-only posts -> requires you to be logged in
        if entry.visibility == Entry.Visibility.FRIENDS:
            if follows and followed_by:
                return render(request, "stream_home.html", {"entries": [entry], "author": author})
            return HttpResponseForbidden("You must be friends with this author to view this post.")
    else:
        return render(request, "stream_home.html", {"entries": [], "author": author})

        
@login_required
def entry_edit(request, author_serial, entry_serial):
    entry = get_object_or_404(Entry, serial=entry_serial)

    if request.user != entry.author.user:
        return HttpResponse("You do not have permission to edit this post.", status=403)

    if request.method == "POST":
        form = EntryForm(request.POST, request.FILES, instance=entry)
        if form.is_valid():
            entry = form.save(commit=False)

            # Handle new image upload
            if 'image_file' in request.FILES:
                uploaded_file = request.FILES['image_file']
                hosted = HostedImage(file=uploaded_file, uploaded_by=request.user)
                hosted.save()
                entry.image_url = request.build_absolute_uri(hosted.file.url)

            # Handle image removal
            elif 'remove_image' in request.POST:
                entry.image_url = None

            entry.save()
            return redirect("entries:stream_home", author_serial=entry.author.serial)
    else:
        form = EntryForm(instance=entry)

    return render(request, "entries/entry_edit.html", {"form": form, "entry": entry})

@login_required
def entry_delete(request, author_serial, entry_serial):
    entry = get_object_or_404(Entry, serial=entry_serial, author__serial=author_serial)
    if request.method == "POST":
        entry.mark_deleted()
        return redirect("entries:stream_home", author_serial=author_serial)
    
    return redirect("entries:entry_edit", author_serial=author_serial, entry_serial=entry_serial)
