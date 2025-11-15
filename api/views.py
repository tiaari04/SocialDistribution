from django.http import JsonResponse
from urllib.parse import unquote
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
import json
from entries import services as entries_services
from inbox import services as followers_services
from inbox import serializers as followers_serializers
from django.contrib.auth.models import User

# followers serializer will use variables to know how to format the data
FOLLOWERS = 1
FOLLOWING = 2
FOLLOW_REQS = 3

def _not_implemented(endpoint_name):
	return JsonResponse({"detail": "not implemented", "endpoint": endpoint_name}, status=501)

# Authors
def api_authors_list(request):
	return _not_implemented("api_authors_list")

def api_author_detail(request, author_serial):
	return _not_implemented("api_author_detail")

def api_author_followers(request, author_serial):
	if request.method != "GET":
		return JsonResponse({"detail": "Method not allowed"}, status=405)

	from authors.models import Author
	author = get_object_or_404(Author, serial=author_serial)
	resp, status_code = followers_serializers.serialize_followers_view(author, FOLLOWERS)
	return JsonResponse(resp, status=status_code)

def api_author_follower_detail(request, author_serial, foreign_encoded):
	if request.method not in ["GET", "PUT", "DELETE"]:
		return JsonResponse({"detail": "Method not allowed"}, status=405)

	from authors.models import Author
	author = get_object_or_404(Author, serial=author_serial)
	actor_fqid = unquote(foreign_encoded)
	actor = get_object_or_404(Author, id=actor_fqid)

	if request.method == "GET":
		result = followers_services.get_follower(author, actor)
		if result:
			return JsonResponse(result)
		return JsonResponse({"is_follower": False}, status=404)
		
	if not request.user.is_authenticated:
		return JsonResponse({"detail": "Authentication required"}, status=403)

	if str(request.user.author.serial) == str(author_serial):

		if request.method == "PUT":
			response = followers_services.add_follower(author, actor)
			if response:
				return JsonResponse({"detail": "Follower added"}, status=201)
			return JsonResponse({"detail": "Follow request doesn't exist"}, status=404)

		elif request.method == "DELETE":
			response = followers_services.remove_follower(author, actor)
			if response:
				return JsonResponse({"detail": "Follower removed"}, status=200)
			return JsonResponse({"detail": "Follower didn't exist"}, status=404)

	# elif str(request.user.author.id) == str(actor_fqid):
	# 	if request.method == "DELETE":
	# 		response = followers_services.remove_follower(author, actor)
	# 		if response:
	# 			return JsonResponse({"detail": "Author unfollowed"}, status=200)
	# 		return JsonResponse({"detail": "You didn't follow this author"}, status=200)

	return JsonResponse({"detail": "Forbidden"}, status=403)

def api_author_follow_requests(request, author_serial):
	if request.method != "GET":
		return JsonResponse({"detail": "Method not allowed"}, status=405)

	from authors.models import Author
	author = get_object_or_404(Author, serial=author_serial)
	resp, status_code = followers_serializers.serialize_followers_view(author, True)
	return JsonResponse(resp, status=status_code)

def api_author_inbox(request, author_serial):
	# Accept POSTs from remote nodes to deliver comments/likes/follows
	if request.method != 'POST':
		return JsonResponse({'detail': 'Method not allowed'}, status=405)

	try:
		payload = json.loads(request.body.decode('utf-8'))
	except Exception:
		return JsonResponse({'detail': 'Invalid JSON'}, status=400)

	result = entries_services.process_inbox_for(author_serial, payload)
	if result.get('status') in ('created', 'exists'):
		return JsonResponse({'detail': 'ok', 'status': result.get('status')}, status=201)
	if result.get('status') == 'ignored':
		return JsonResponse({'detail': 'ignored'}, status=200)
	return JsonResponse({'detail': 'error', 'error': result.get('error')}, status=400)

# Entries
def api_author_entries(request, author_serial):
	return _not_implemented("api_author_entries")

def api_author_entry_detail(request, author_serial, entry_serial):
	return _not_implemented("api_author_entry_detail")

def api_author_entry_image(request, author_serial, entry_serial):
	return _not_implemented("api_author_entry_image")

def api_entry_by_fqid(request, entry_fqid):
	return _not_implemented("api_entry_by_fqid")

def api_entry_image(request, entry_fqid):
	return _not_implemented("api_entry_image")

# Comments & Likes (per-entry serial)
def api_entry_comments(request, author_serial, entry_serial):
	# delegate to entries.api_views EntryCommentsViewSet
	from entries.api_views import EntryCommentsViewSet
	view = EntryCommentsViewSet.as_view({'get': 'list', 'post': 'create'})
	return view(request, author_serial=author_serial, entry_serial=entry_serial)

def api_entry_likes(request, author_serial, entry_serial):
	from entries.api_views import EntryLikesViewSet
	view = EntryLikesViewSet.as_view({'get': 'list', 'post': 'create'})
	return view(request, author_serial=author_serial, entry_serial=entry_serial)

# ENTRY FQID based endpoints
def api_entry_comments_by_fqid(request, entry_fqid):
	from entries.api_views import EntryCommentsViewSet
	view = EntryCommentsViewSet.as_view({'get': 'list', 'post': 'create'})
	return view(request, entry_fqid=entry_fqid)

def api_entry_likes_by_fqid(request, entry_fqid):
	from entries.api_views import EntryLikesViewSet
	view = EntryLikesViewSet.as_view({'get': 'list', 'post': 'create'})
	return view(request, entry_fqid=entry_fqid)

# Liked / Commented lists
def api_author_liked(request, author_serial):
	return _not_implemented("api_author_liked")

def api_author_commented(request, author_serial):
	return _not_implemented("api_author_commented")

# Comment detail and likes on comment
def api_entry_comment_detail(request, author_serial, entry_serial, comment_fqid):
	# Return a single comment (delegates to Entries comment list view for GET)
	from entries.api_views import EntryCommentsViewSet
	view = EntryCommentsViewSet.as_view({'get': 'list'})
	return view(request, author_serial=author_serial, entry_serial=entry_serial)

def api_entry_comment_likes(request, author_serial, entry_serial, comment_fqid):
	from entries.api_views import CommentLikesViewSet
	view = CommentLikesViewSet.as_view({'get': 'list', 'post': 'create'})
	return view(request, author_serial=author_serial, entry_serial=entry_serial, comment_fqid=comment_fqid)

# Global FQID endpoints
def api_comment_by_fqid(request, comment_fqid):
	return _not_implemented("api_comment_by_fqid")

def api_like_by_fqid(request, like_fqid):
	return _not_implemented("api_like_by_fqid")

# Stream & public
def api_stream(request):
	return _not_implemented("api_stream")

def api_public_entries(request):
	return _not_implemented("api_public_entries")

# Additional stubs for FQID/serial lookups
def api_author_by_fqid(request, author_fqid):
	return _not_implemented("api_author_by_fqid")

def api_author_by_fqid_liked(request, author_fqid):
	return _not_implemented("api_author_by_fqid_liked")

def api_author_by_fqid_commented(request, author_fqid):
	return _not_implemented("api_author_by_fqid_commented")

def api_author_liked_detail(request, author_serial, like_serial):
	return _not_implemented("api_author_liked_detail")

def api_author_commented_detail(request, author_serial, comment_serial):
	return _not_implemented("api_author_commented_detail")