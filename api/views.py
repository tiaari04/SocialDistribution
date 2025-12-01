from django.http import JsonResponse
from urllib.parse import unquote
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
import json
from entries import services as entries_services
from inbox import services as followers_services
from inbox import serializers as followers_serializers
from django.contrib.auth.models import User
from federation.utils import check_basic_auth, create_remote_author
from codecs import decode
from federation.utils import check_basic_auth
from authors.models import Author
from django.utils.dateparse import parse_datetime
from authors.models import Author
from inbox.models import FollowRequest
from inbox.models import InboxItem

# followers serializer will use variables to know how to format the data
FOLLOWERS = 1
FOLLOW_REQS = 2
FOLLOWING = 3

def _not_implemented(endpoint_name):
	return JsonResponse({"detail": "not implemented", "endpoint": endpoint_name}, status=501)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from authors.models import Author
from django.core.serializers import serialize

@csrf_exempt
def api_authors_list(request):
	if request.method == "GET":
		authors = Author.objects.filter(is_local=True)
		data = [
            {
                "id": str(author.id),
                "serial": author.serial,
                "displayName": author.displayName,
                "github": author.github,
                "host": author.host,
                "profileImage": author.profileImage,
                "description": author.description,
                "web": author.web,
                "is_active": author.is_active,
                "is_admin": author.is_admin,
                "is_approved": author.is_approved,
                "is_local": author.is_local,
                "created": author.created.isoformat() if author.created else None,
                "updated": author.updated.isoformat() if author.updated else None,
            }
            for author in authors
        ]
		return JsonResponse({"items": data}, status=200)
	return JsonResponse({"detail": "Method not allowed"}, status=405)

@csrf_exempt
def api_author_detail(request, author_serial):
    if request.method == "GET":
        # Return author detail as JSON
        try:
            author = Author.objects.get(serial=author_serial)
        except Author.DoesNotExist:
            return JsonResponse({"error": "Author not found"}, status=404)

        data = {
            "id": str(author.id),
            "serial": author.serial,
            "displayName": author.displayName,
            "github": author.github,
            "host": author.host,
            "profileImage": author.profileImage,
            "description": author.description,
            "web": author.web,
            "is_active": author.is_active,
            "is_admin": author.is_admin,
            "is_approved": author.is_approved,
            "is_local": author.is_local,
            "created": author.created.isoformat() if author.created else None,
            "updated": author.updated.isoformat() if author.updated else None,
        }
        return JsonResponse(data, status=200)

def api_author_followers(request, author_serial):
	if request.method != "GET":
		return JsonResponse({"detail": "Method not allowed"}, status=405)

	from authors.models import Author
	author = get_object_or_404(Author, serial=author_serial)

	if not request.user.is_authenticated or str(request.user.author.serial) != str(author_serial):
		return JsonResponse({"detail": "Authentication required"}, status=403)

	resp, status_code = followers_serializers.serialize_followers_view(author, FOLLOWERS)
	return JsonResponse(resp, status=status_code)

def api_author_follower_detail(request, author_serial, foreign_encoded):
	if request.method not in ["GET", "PUT", "DELETE"]:
		return JsonResponse({"detail": "Method not allowed"}, status=405)

	from authors.models import Author
	author = get_object_or_404(Author, serial=author_serial)
	actor_fqid = decode(foreign_encoded, 'unicode_escape')
	actor_fqid = unquote(actor_fqid)
	actor = get_object_or_404(Author, id=actor_fqid)
		
	if not request.user.is_authenticated or str(request.user.author.serial) != str(author_serial):
		return JsonResponse({"detail": "Authentication required"}, status=403)

	if request.method == "GET":
		result = followers_services.get_follower(author, actor)
		if result:
			return JsonResponse(result)
		return JsonResponse({"is_follower": False}, status=404)

	elif request.method == "PUT":
		response = followers_services.add_follower(author, actor)
		if response:
			return JsonResponse({"detail": "Follower added"}, status=201)
		return JsonResponse({"detail": "Follow request doesn't exist"}, status=404)

	elif request.method == "DELETE":
		response = followers_services.remove_follower(author, actor)
		if response:
			return JsonResponse({"detail": "Follower removed"}, status=200)
		return JsonResponse({"detail": "Follower doesn't exist"}, status=404)

def api_author_following(request, author_serial):
	if request.method != "GET":
		return JsonResponse({"detail": "Method not allowed"}, status=405)

	from authors.models import Author
	author = get_object_or_404(Author, serial=author_serial)

	if not request.user.is_authenticated or str(request.user.author.serial) != str(author_serial):
		return JsonResponse({"detail": "Authentication required"}, status=403)

	resp, status_code = followers_serializers.serialize_followers_view(author, FOLLOWING)
	return JsonResponse(resp, status=status_code)

def api_author_following_detail(request, author_serial, foreign_serial):
    if request.method not in ["GET", "PUT", "DELETE"]:
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    
    author = get_object_or_404(Author, serial=author_serial)
    
    foreign_author = get_object_or_404(Author, serial=foreign_serial)
    
    if not request.user.is_authenticated or str(request.user.author.serial) != str(author_serial):
        return JsonResponse({"detail": "Authentication required"}, status=403)
    
    if request.method == "GET":
        result = followers_services.get_followed_author(author, foreign_author)
        if result:
            return JsonResponse(result)
        return JsonResponse({"is_following": False}, status=404)
    
    elif request.method == "PUT":
        response = followers_services.add_followed_author(author, foreign_author)
        if response.get("details") == "exists":
            return JsonResponse({"detail": "Follow request already exists"}, status=200)
        if response.get("details") == "created":
            return JsonResponse({"detail": "Follow request sent"}, status=201)
    
    elif request.method == "DELETE":
        if not author.is_local() or not foreign_author.is_local():
            return JsonResponse({"detail": "Cannot unfollow remote authors"}, status=403)
        
        response = followers_services.remove_followed_author(author, foreign_author)
        if response:
            return JsonResponse({"detail": "Author unfollowed"}, status=200)
        return JsonResponse({"detail": "You didn't follow this author"}, status=404)

def api_author_follow_requests(request, author_serial):
	if request.method != "GET":
		return JsonResponse({"detail": "Method not allowed"}, status=405)

	from authors.models import Author
	author = get_object_or_404(Author, serial=author_serial)
	resp, status_code = followers_serializers.serialize_followers_view(author, FOLLOW_REQS)
	return JsonResponse(resp, status=status_code)

@csrf_exempt
def api_author_inbox(request, author_serial):
	# Accept POSTs from remote nodes to deliver comments/likes/follows
	if request.method != 'POST':
		return JsonResponse({'detail': 'Method not allowed'}, status=405)

	print(author_serial)
	
	"""if request.user.is_authenticated:
		try:
			if str(request.user.author.serial) != str(author_serial):
				node = None
			else:
				return JsonResponse({"error": "Forbidden: You may only post to your own inbox."}, status=403)
		except AttributeError:
			return JsonResponse({"error": "Forbidden: User profile missing author mapping."}, status=403)
	else:
		node = check_basic_auth(request)
		print("basic auth: ", node)
		if not node:
			return JsonResponse({"error": "Unauthorized"}, status=401)"""
	try:
		payload = json.loads(request.body.decode('utf-8'))
	except Exception:
		return JsonResponse({'detail': 'Invalid JSON'}, status=400)
	
	print("REACHED ENDPOINT")
	print(payload)
	result = entries_services.process_inbox_for(author_serial, payload)
	if result.get('status') in ('created', 'exists'):
		return JsonResponse({'detail': 'ok', 'status': result.get('status')}, status=201)
	if result.get('status') == 'ignored':
		return JsonResponse({'detail': 'ignored'}, status=200)
	return JsonResponse({'detail': 'error', 'error': result.get('error')}, status=400)

# Entries
def api_author_entries(request, author_serial):
	"""GET /api/authors/{author_serial}/entries/ - Returns all entries for an author"""
	if request.method != 'GET':
		return JsonResponse({'detail': 'Method not allowed'}, status=405)
	
	author = get_object_or_404(Author, serial=author_serial)
	
	from entries.models import Entry
	from entries.serializers import EntrySerializer
	
	# Get all non-deleted entries by this author, ordered by published date
	entries = Entry.objects.filter(author=author).exclude(visibility=Entry.Visibility.DELETED).order_by('-published')
	
	serializer = EntrySerializer(entries, many=True)
	
	return JsonResponse({
		'type': 'entries',
		'items': serializer.data
	}, status=200)

def api_author_entry_detail(request, author_serial, entry_serial):
	"""GET single entry by author_serial and entry_serial"""
	if request.method != 'GET':
		return JsonResponse({'detail': 'Method not allowed'}, status=405)
	
	author = get_object_or_404(Author, serial=author_serial)
	from entries.models import Entry
	from entries.serializers import EntrySerializer
	
	entry = get_object_or_404(Entry, author=author, serial=entry_serial)
	if entry.visibility == Entry.Visibility.DELETED:
		return JsonResponse({'detail': 'Not found'}, status=404)
	
	serializer = EntrySerializer(entry)
	return JsonResponse(serializer.data, status=200)

def api_author_entry_image(request, author_serial, entry_serial):
	"""GET entry image URL by author_serial and entry_serial"""
	if request.method != 'GET':
		return JsonResponse({'detail': 'Method not allowed'}, status=405)
	
	author = get_object_or_404(Author, serial=author_serial)
	from entries.models import Entry
	
	entry = get_object_or_404(Entry, author=author, serial=entry_serial)
	if entry.visibility == Entry.Visibility.DELETED:
		return JsonResponse({'detail': 'Not found'}, status=404)
	
	if not entry.image_url:
		return JsonResponse({'detail': 'No image'}, status=404)
	
	return JsonResponse({'image_url': entry.image_url}, status=200)

def api_entry_by_fqid(request, entry_fqid):
	"""GET single entry by FQID"""
	if request.method != 'GET':
		return JsonResponse({'detail': 'Method not allowed'}, status=405)
	
	from entries.models import Entry
	from entries.serializers import EntrySerializer
	
	# Decode FQID if needed
	decoded_fqid = unquote(entry_fqid)
	
	entry = get_object_or_404(Entry, fqid=decoded_fqid)
	if entry.visibility == Entry.Visibility.DELETED:
		return JsonResponse({'detail': 'Not found'}, status=404)
	
	serializer = EntrySerializer(entry)
	return JsonResponse(serializer.data, status=200)

def api_entry_image(request, entry_fqid):
	"""GET entry image URL by FQID"""
	if request.method != 'GET':
		return JsonResponse({'detail': 'Method not allowed'}, status=405)
	
	from entries.models import Entry
	
	# Decode FQID if needed
	decoded_fqid = unquote(entry_fqid)
	
	entry = get_object_or_404(Entry, fqid=decoded_fqid)
	if entry.visibility == Entry.Visibility.DELETED:
		return JsonResponse({'detail': 'Not found'}, status=404)
	
	if not entry.image_url:
		return JsonResponse({'detail': 'No image'}, status=404)
	
	return JsonResponse({'image_url': entry.image_url}, status=200)

# Comments & Likes (per-entry serial)
@csrf_exempt
def api_entry_comments(request, author_serial, entry_serial):
	# delegate to entries.api_views EntryCommentsViewSet
	from entries.api_views import EntryCommentsViewSet
	view = EntryCommentsViewSet.as_view({'get': 'list', 'post': 'create'})
	return view(request, author_serial=author_serial, entry_serial=entry_serial)

@csrf_exempt
def api_entry_likes(request, author_serial, entry_serial):
	from entries.api_views import EntryLikesViewSet
	view = EntryLikesViewSet.as_view({'get': 'list', 'post': 'create'})
	return view(request, author_serial=author_serial, entry_serial=entry_serial)

# ENTRY FQID based endpoints
@csrf_exempt
def api_entry_comments_by_fqid(request, entry_fqid):
	from entries.api_views import EntryCommentsViewSet
	view = EntryCommentsViewSet.as_view({'get': 'list', 'post': 'create'})
	return view(request, entry_fqid=entry_fqid)

@csrf_exempt
def api_entry_likes_by_fqid(request, entry_fqid):
	from entries.api_views import EntryLikesViewSet
	view = EntryLikesViewSet.as_view({'get': 'list', 'post': 'create'})
	return view(request, entry_fqid=entry_fqid)

# Liked / Commented lists
def api_author_liked(request, author_serial):
	"""GET all things an author has liked"""
	if request.method != 'GET':
		return JsonResponse({'detail': 'Method not allowed'}, status=405)
	
	author = get_object_or_404(Author, serial=author_serial)
	from entries.models import Like
	from entries.serializers import LikeSerializer
	
	likes = Like.objects.filter(author=author).order_by('-published')
	serializer = LikeSerializer(likes, many=True)
	
	return JsonResponse({
		'type': 'liked',
		'items': serializer.data
	}, status=200)

def api_author_commented(request, author_serial):
	"""GET all comments by an author"""
	if request.method != 'GET':
		return JsonResponse({'detail': 'Method not allowed'}, status=405)
	
	author = get_object_or_404(Author, serial=author_serial)
	from entries.models import Comment
	from entries.serializers import CommentSerializer
	
	comments = Comment.objects.filter(author=author).order_by('-published')
	serializer = CommentSerializer(comments, many=True)
	
	return JsonResponse({
		'type': 'comments',
		'items': serializer.data
	}, status=200)

# Comment detail and likes on comment
def api_entry_comment_detail(request, author_serial, entry_serial, comment_fqid):
	# Return a single comment (delegates to Entries comment list view for GET)
	from entries.api_views import EntryCommentsViewSet
	view = EntryCommentsViewSet.as_view({'get': 'list'})
	return view(request, author_serial=author_serial, entry_serial=entry_serial)

@csrf_exempt
def api_entry_comment_likes(request, author_serial, entry_serial, comment_fqid):
	from entries.api_views import CommentLikesViewSet
	view = CommentLikesViewSet.as_view({'get': 'list', 'post': 'create'})
	return view(request, author_serial=author_serial, entry_serial=entry_serial, comment_fqid=comment_fqid)

# Global FQID endpoints
def api_comment_by_fqid(request, comment_fqid):
	"""GET single comment by FQID"""
	if request.method != 'GET':
		return JsonResponse({'detail': 'Method not allowed'}, status=405)
	
	from entries.models import Comment
	from entries.serializers import CommentSerializer
	
	# Decode FQID if needed
	decoded_fqid = unquote(comment_fqid)
	
	comment = get_object_or_404(Comment, fqid=decoded_fqid)
	serializer = CommentSerializer(comment)
	return JsonResponse(serializer.data, status=200)

def api_like_by_fqid(request, like_fqid):
	"""GET single like by FQID"""
	if request.method != 'GET':
		return JsonResponse({'detail': 'Method not allowed'}, status=405)
	
	from entries.models import Like
	from entries.serializers import LikeSerializer
	
	# Decode FQID if needed
	decoded_fqid = unquote(like_fqid)
	
	like = get_object_or_404(Like, fqid=decoded_fqid)
	serializer = LikeSerializer(like)
	return JsonResponse(serializer.data, status=200)

# Stream & public
def api_stream(request):
	"""GET user's personalized feed/stream"""
	if request.method != 'GET':
		return JsonResponse({'detail': 'Method not allowed'}, status=405)
	
	# For now, return all public entries (can be enhanced with following/friends logic)
	from entries.models import Entry
	from entries.serializers import EntrySerializer
	
	entries = Entry.objects.filter(
		visibility=Entry.Visibility.PUBLIC
	).exclude(visibility=Entry.Visibility.DELETED).order_by('-published')[:50]
	
	serializer = EntrySerializer(entries, many=True)
	
	return JsonResponse({
		'type': 'stream',
		'items': serializer.data
	}, status=200)

def api_public_entries(request):
	"""GET all public entries - used by federation to discover posts"""
	if request.method != 'GET':
		return JsonResponse({'detail': 'Method not allowed'}, status=405)
	
	from entries.models import Entry
	from entries.serializers import EntrySerializer
	
	# Get all public, non-deleted entries
	entries = Entry.objects.filter(
		visibility=Entry.Visibility.PUBLIC
	).exclude(visibility=Entry.Visibility.DELETED).order_by('-published')
	
	serializer = EntrySerializer(entries, many=True)
	
	return JsonResponse({
		'type': 'entries',
		'items': serializer.data
	}, status=200)

# Additional stubs for FQID/serial lookups
def api_author_by_fqid(request, author_fqid):
	"""GET author by FQID"""
	if request.method != 'GET':
		return JsonResponse({'detail': 'Method not allowed'}, status=405)
	
	# Decode FQID if needed
	decoded_fqid = unquote(author_fqid)
	
	author = get_object_or_404(Author, id=decoded_fqid)
	
	return JsonResponse({
		'type': 'author',
		'id': author.id,
		'serial': author.serial,
		'displayName': author.displayName,
		'host': author.host,
		'web': author.web,
		'profileImage': author.profileImage
	}, status=200)

def api_author_by_fqid_liked(request, author_fqid):
	"""GET what an author (by FQID) has liked"""
	if request.method != 'GET':
		return JsonResponse({'detail': 'Method not allowed'}, status=405)
	
	# Decode FQID if needed
	decoded_fqid = unquote(author_fqid)
	
	author = get_object_or_404(Author, id=decoded_fqid)
	from entries.models import Like
	from entries.serializers import LikeSerializer
	
	likes = Like.objects.filter(author=author).order_by('-published')
	serializer = LikeSerializer(likes, many=True)
	
	return JsonResponse({
		'type': 'liked',
		'items': serializer.data
	}, status=200)

def api_author_by_fqid_commented(request, author_fqid):
	"""GET what an author (by FQID) has commented"""
	if request.method != 'GET':
		return JsonResponse({'detail': 'Method not allowed'}, status=405)
	
	# Decode FQID if needed
	decoded_fqid = unquote(author_fqid)
	
	author = get_object_or_404(Author, id=decoded_fqid)
	from entries.models import Comment
	from entries.serializers import CommentSerializer
	
	comments = Comment.objects.filter(author=author).order_by('-published')
	serializer = CommentSerializer(comments, many=True)
	
	return JsonResponse({
		'type': 'comments',
		'items': serializer.data
	}, status=200)

def api_author_liked_detail(request, author_serial, like_serial):
	"""GET specific like by author and like identifier"""
	if request.method != 'GET':
		return JsonResponse({'detail': 'Method not allowed'}, status=405)
	
	author = get_object_or_404(Author, serial=author_serial)
	from entries.models import Like
	from entries.serializers import LikeSerializer
	
	# Try to find like by serial pattern in FQID
	likes = Like.objects.filter(author=author, fqid__contains=like_serial)
	if not likes.exists():
		return JsonResponse({'detail': 'Not found'}, status=404)
	
	like = likes.first()
	serializer = LikeSerializer(like)
	return JsonResponse(serializer.data, status=200)

def api_author_commented_detail(request, author_serial, comment_serial):
	"""GET specific comment by author and comment identifier"""
	if request.method != 'GET':
		return JsonResponse({'detail': 'Method not allowed'}, status=405)
	
	author = get_object_or_404(Author, serial=author_serial)
	from entries.models import Comment
	from entries.serializers import CommentSerializer
	
	# Try to find comment by serial pattern in FQID
	comments = Comment.objects.filter(author=author, fqid__contains=comment_serial)
	if not comments.exists():
		return JsonResponse({'detail': 'Not found'}, status=404)
	
	comment = comments.first()
	serializer = CommentSerializer(comment)
	return JsonResponse(serializer.data, status=200)