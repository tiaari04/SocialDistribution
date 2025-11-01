from django.http import HttpResponse, JsonResponse
from .models import Entry
from authors.models import Author
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .forms import EntryForm
from django.utils import timezone
import uuid
from django.contrib.auth.decorators import login_required

def stream_home(request, author_serial):
    entries = []
    entry_objs = Entry.objects.exclude(visibility='DELETED') 
    # gets all the saved added entries from the database that AREN'T deleted
    author = get_object_or_404(Author, serial=author_serial)
    
    return render(request, "stream_home.html", { "entries": entry_objs, "author" : author })

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

            # generate a short unique serial and full FQID (adjust host as needed)
            entry.serial = uuid.uuid4().hex[:12]
            # Use the author's host if available; fallback to example.com
            host = author.host.rstrip("/") if getattr(author, "host", None) else "http://127.0.0.1:8000"
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
    return render(request, "stream_home.html", {"entries": [entry], "author": author})
        
def entry_edit(request, author_serial, entry_serial):
    entry = get_object_or_404(Entry, serial=entry_serial)

    # Check ownership
    if request.user != entry.author.user:
        return HttpResponse("You do not have permission to edit this post.", status=403)

    if request.method == "POST":
        form = EntryForm(request.POST, request.FILES, instance=entry)
        if form.is_valid():
            form.save()
            # Redirect to stream_home with the author_serial of the post
            return redirect("entries:stream_home", author_serial=entry.author.serial)
    else:
        form = EntryForm(instance=entry)

    return render(request, "entries/entry_edit.html", {"form": form, "entry": entry})

def entry_delete(request, author_serial, entry_serial):
    entry = get_object_or_404(Entry, serial=entry_serial, author__serial=author_serial)
    if request.method == "POST":
        entry.delete()
        return redirect("entries:stream_home", author_serial=author_serial)
    
    return redirect("entries:entry_edit", author_serial=author_serial, entry_serial=entry_serial)
