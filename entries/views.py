from django.http import HttpResponse, JsonResponse
from .models import Entry
from authors.models import Author
from django.shortcuts import render, redirect
from django.urls import reverse

def stream_home(request):
    entries = []
    # IDs not being automatically set 
    #new_entry = Entry(title='title', content='content', fqid='', author=author_obj)
    entry_objs = Entry.objects.exclude(visibility='DELETED') 
    print(Entry.objects.get(fqid='5').author.displayName)
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
            # 'comments': entry.comments
        })
        # makes the list of pages to display in index.html
    return render(request, "stream_home.html", { "entries": entries })

def like_post(request): 
    # return redirect(stream_home)
    # api_views.EntryLikesViewSet
    # models.increment_like_count signals Entry like_count to update? 
    # entries/<path:entry_fqid>/likes/
    return redirect('entries:stream_home')

def add_comment(request): 
    # return redirect(stream_home)
    # api_views.EntryCommentsViewSet
    # entries/<path:entry_fqid>/comments/
    return HttpResponse("add comment (not implemented)")

def like_comment(request): 
    # return redirect(stream_home)
    # api_views.EntryCommentLikesViewSet
        # endpoints are supposed to call api_views functions?
        # authors/<str:author_serial>/entries/<str:entry_serial>/comments/<path:comment_fqid>/likes/
    return HttpResponse("add comment like (not implemented)")

def public_entries(request):
	return HttpResponse("public entries (not implemented)")

def entry_create(request):
	return HttpResponse("entry create (not implemented)")

def entry_detail(request, entry_serial):
	return HttpResponse(f"entry detail {entry_serial} (not implemented)")

def entry_edit(request, entry_serial):
	return HttpResponse(f"entry edit {entry_serial} (not implemented)")
