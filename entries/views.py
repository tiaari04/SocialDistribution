from django.forms import model_to_dict
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse
from inbox.models import FollowRequest
from .models import Entry
from authors.models import Author
from django.shortcuts import render, redirect, get_object_or_404
from .forms import EntryForm
from django.utils import timezone
import uuid

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


def entry_create(request, author_serial):
    author = get_object_or_404(Author, serial=author_serial)

    if request.method == "POST":
        form = EntryForm(request.POST, request.FILES or None)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.author = author

            entry.serial = uuid.uuid4().hex[:12]
            
            host = author.host.rstrip("/") if getattr(author, "host", None) else "https://example.com"
            entry.fqid = f"{host}/authors/{author.serial}/entries/{entry.serial}"

            entry.published = timezone.now()
            entry.save()
            return redirect("entries:stream_home", author_serial=author.serial)
    else:
        form = EntryForm()

    return render(request, "entries/entry_form.html", {"form": form, "author": author})


def entry_detail(request, author_serial, entry_serial):
    author = get_object_or_404(Author, serial=author_serial)
    entry = get_object_or_404(Entry, author=author, serial=entry_serial)
    return render(request, "entries/entry_detail.html", {"entry": entry})

def entry_edit(request, author_serial, entry_serial):
    entry = get_object_or_404(Entry, serial=entry_serial)

    # Check ownership
    if request.user != entry.author.user:
        return HttpResponse("You do not have permission to edit this post.", status=403)

    if request.method == "POST":
        form = EntryForm(request.POST, request.FILES, instance=entry)
        if form.is_valid():
            form.save()
            return redirect("entries:stream_home", author_serial=entry.author.serial)
    else:
        form = EntryForm(instance=entry)

    return render(request, "entries/entry_edit.html", {"form": form, "entry": entry})

def entry_delete(request, author_serial, entry_serial):
    entry = get_object_or_404(Entry, serial=entry_serial, author__serial=author_serial)
    if request.method == "POST":
        entry.mark_deleted()
        return redirect("entries:stream_home", author_serial=author_serial)
    
    return redirect("entries:entry_edit", author_serial=author_serial, entry_serial=entry_serial)
