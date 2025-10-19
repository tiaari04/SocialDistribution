from django.http import HttpResponse, JsonResponse
from .models import Entry
from authors.models import Author
from django.shortcuts import render

def stream_home(request):
    entries = []
    # IDs not being automatically set 
    #new_entry = Entry(title='title', content='content', fqid='', author=author_obj)
    entry_objs = Entry.objects.exclude(visibility='DELETED') 
    # gets all the saved added entries from the database that AREN'T deleted
    for entry in entry_objs:
        entries.append({
            "title": entry.title,
            "content": entry.content,
            "published": entry.published,
            "author": entry.author,
            "fqid": entry.fqid,
            # "likeCount": entry.likeCount,
            # 'commentCount': entry.commentCount.
            # 'comments': entry.comments
        })
        # makes the list of pages to display in index.html
    # TODO: sort the entries list so that most recent (including edited) show at the top
    return render(request, "stream_home.html", { "entries": entries })

def public_entries(request):
	return HttpResponse("public entries (not implemented)")

def entry_create(request):
	return HttpResponse("entry create (not implemented)")

def entry_detail(request, entry_serial):
	return HttpResponse(f"entry detail {entry_serial} (not implemented)")

def entry_edit(request, entry_serial):
	return HttpResponse(f"entry edit {entry_serial} (not implemented)")
