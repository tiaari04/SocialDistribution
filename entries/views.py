from django.http import HttpResponse, JsonResponse
from .models import Entry
from authors.models import Author
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

def stream_home(request, author_serial):
    entries = []
    entry_objs = Entry.objects.exclude(visibility='DELETED') 
    # gets all the saved added entries from the database that AREN'T deleted
    for entry in entry_objs:
        entries.append({
            "title": entry.title,
            "content": entry.content,
            "published": entry.published,
            "author": entry.author,
            "fqid": entry.fqid,
            "likeCount": entry.likes_count,
            'serial': entry.serial,
        })
        # makes the list of pages to display in index.html
	
    author = get_object_or_404(Author, serial=author_serial)
    return render(request, "stream_home.html", { "entries": entries, "author" : author })

def public_entries(request):
	return HttpResponse("public entries (not implemented)")

def entry_create(request):
	return HttpResponse("entry create (not implemented)")

def entry_detail(request, entry_serial):
	return HttpResponse(f"entry detail {entry_serial} (not implemented)")

def entry_edit(request, entry_serial):
	return HttpResponse(f"entry edit {entry_serial} (not implemented)")
