from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from.models import Author
from inbox.models import FollowRequest

def author_list(request):
	return HttpResponse("author list (not implemented)")

def author_create(request):
	return HttpResponse("author create (not implemented)")

def author_detail(request, author_serial):
	return HttpResponse(f"author detail {author_serial} (not implemented)")

def author_edit(request, author_serial):
	return HttpResponse(f"author edit {author_serial} (not implemented)")

def author_entries_page(request, author_serial):
	return HttpResponse(f"author entries {author_serial} (not implemented)")

def author_followers_page(request, author_serial):
	return HttpResponse(f"author followers {author_serial} (not implemented)")

def follow_requests_page(request, author_serial):
	author = get_object_or_404(Author, serial=author_serial)

	requests = FollowRequest.objects.filter(author_followed=author, state=FollowRequest.State.REQUESTING).select_related('actor')

	context = {"author": author, "requests": requests}

	return render(request, "follow_requests.html", context)