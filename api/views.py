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
		authors = Author.objects.all()
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

def api_author_following_detail(request, author_serial, foreign_encoded):
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
		result = followers_services.get_followed_author(author, actor)
		if result:
			return JsonResponse(result)
		return JsonResponse({"is_following": False}, status=404)

	elif request.method == "PUT":
		response = followers_services.add_followed_author(author, actor)
		if response["details"] == "exists":
			return JsonResponse({"detail": "Follow request already exists"}, status=200)
		if response["details"] == "created":
			return JsonResponse({"detail": "Follow request sent"}, status=201)

	elif request.method == "DELETE":
		response = followers_services.remove_followed_author(author, actor)
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
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8"))
        print("INBOX PAYLOAD:", payload)
    except Exception:
        return JsonResponse({"detail": "Invalid JSON"}, status=400)

    payload_type = (payload.get("type") or "").lower()

    try:
        recipient = Author.objects.get(serial=author_serial)
    except Author.DoesNotExist:
        return JsonResponse({"detail": "Recipient does not exist"}, status=404)

    # -------- FOLLOW / FOLLOWREQUEST --------
    if payload_type in ["follow", "followrequest"]:
        try:
            actor_data = payload.get("actor")
            object_data = payload.get("object")

            if not actor_data or not object_data:
                return JsonResponse({"detail": "Missing actor/object"}, status=400)

            # Extract actor serial
            actor_id = actor_data.get("id")
            actor_serial = actor_id.split("/")[-1] if actor_id else None

            object_id = object_data.get("id")
            object_serial = object_id.split("/")[-1] if object_id else None

            if not actor_serial or not object_serial:
                return JsonResponse({"detail": "Invalid actor/object IDs"}, status=400)

            # Upsert ACTOR author (remote user who wants to follow)
            actor_defaults = {
                "displayName": actor_data.get("displayName", ""),
                "github": actor_data.get("github", ""),
                "host": actor_data.get("host", ""),
                "profileImage": actor_data.get("profileImage", ""),
                "web": actor_data.get("web", ""),
                "is_active": True,
                "is_admin": False,
                "is_approved": True,
                "is_local": False,
            }
            actor_obj, _ = Author.objects.update_or_create(
                serial=actor_serial,
                defaults=actor_defaults,
            )

            # Optional: upsert the "object" author (their view of us)
            object_defaults = {
                "displayName": object_data.get("displayName", ""),
                "github": object_data.get("github", ""),
                "host": object_data.get("host", ""),
                "profileImage": object_data.get("profileImage", ""),
                "web": object_data.get("web", ""),
                "is_active": True,
                "is_admin": False,
                "is_approved": True,
                "is_local": False,
            }
            Author.objects.update_or_create(
                serial=object_serial,
                defaults=object_defaults,
            )

            fr, created = FollowRequest.objects.get_or_create(
                actor=actor_obj,
                author_followed=recipient,
                defaults={"state": FollowRequest.State.REQUESTING},
            )

            # Log raw inbox item, but don't let logging errors break the request
            try:
                InboxItem.objects.create(
                    recipient=recipient,
                    type="follow",
                    object_fqid=object_id,
                    payload=payload,
                )
            except Exception as log_err:
                # You can print or log this if you want
                print(f"[INBOX] Failed to log InboxItem: {log_err}")

            return JsonResponse(
                {
                    "detail": "follow request processed",
                    "created": created,
                },
                status=201 if created else 200,
            )

        except Exception as e:
            return JsonResponse({"detail": f"Follow request error: {e}"}, status=400)

    # -------- COMMENT (local + federated, entry FQID based) --------
    elif payload_type == "comment":
        from entries.api_views import EntryCommentsViewSet

        # Upsert actor author (same pattern as follow)
        actor_data = payload.get("author") or payload.get("actor")
        if actor_data:
            actor_id = actor_data.get("id")
            actor_serial = actor_data.get("serial") or (actor_id.split("/")[-1] if actor_id else None)
            if actor_serial:
                defaults = {
                    "displayName": actor_data.get("displayName", ""),
                    "github": actor_data.get("github", ""),
                    "host": actor_data.get("host", ""),
                    "profileImage": actor_data.get("profileImage", ""),
                    "description": actor_data.get("description", ""),
                    "web": actor_data.get("web", actor_data.get("url", "")),
                    "is_active": True,
                    "is_admin": False,
                    "is_approved": True,
                    "is_local": False,
                }
                author_obj, created = Author.objects.update_or_create(
                    serial=actor_serial,
                    defaults=defaults,
                )
                # optional timestamps if present
                created_dt = parse_datetime(actor_data.get("created")) if actor_data.get("created") else None
                updated_dt = parse_datetime(actor_data.get("updated")) if actor_data.get("updated") else None
                if created_dt:
                    author_obj.created = created_dt
                if updated_dt:
                    author_obj.updated = updated_dt
                author_obj.save()

        entry_fqid = payload.get("entry") or payload.get("object")
        if not entry_fqid:
            return JsonResponse({"detail": "Missing entry FQID for comment"}, status=400)

        # Delegate to the same DRF viewset used by /api/entries/<fqid>/comments/
        view = EntryCommentsViewSet.as_view({"get": "list", "post": "create"})
        return view(request, entry_fqid=entry_fqid)

    # -------- LIKE (entry or comment) --------
    elif payload_type == "like":
        from urllib.parse import urlparse
        from entries.api_views import EntryLikesViewSet, CommentLikesViewSet

        # Upsert actor author (same pattern as comment)
        actor_data = payload.get("author") or payload.get("actor")
        if actor_data:
            actor_id = actor_data.get("id")
            actor_serial = actor_data.get("serial") or (actor_id.split("/")[-1] if actor_id else None)
            if actor_serial:
                defaults = {
                    "displayName": actor_data.get("displayName", ""),
                    "github": actor_data.get("github", ""),
                    "host": actor_data.get("host", ""),
                    "profileImage": actor_data.get("profileImage", ""),
                    "description": actor_data.get("description", ""),
                    "web": actor_data.get("web", actor_data.get("url", "")),
                    "is_active": True,
                    "is_admin": False,
                    "is_approved": True,
                    "is_local": False,
                }
                Author.objects.update_or_create(
                    serial=actor_serial,
                    defaults=defaults,
                )

        obj_fqid = payload.get("object")
        if not obj_fqid:
            return JsonResponse({"detail": "Missing object FQID for like"}, status=400)

        # Comment likes vs entry likes:
        # comment FQIDs are expected to look like:
        #   /authors/<author_serial>/entries/<entry_serial>/comments/<comment_serial>
        parsed = urlparse(obj_fqid)
        parts = parsed.path.strip("/").split("/")

        if "comments" in parts:
            # ----- comment like -----
            try:
                # Expect: ['authors', '<author_serial>', 'entries', '<entry_serial>', 'comments', '<comment_serial>']
                if len(parts) < 6 or parts[0] != "authors" or parts[2] != "entries" or parts[4] != "comments":
                    raise ValueError("Unexpected comment FQID path structure")
                author_serial_path = parts[1]
                entry_serial_path = parts[3]
            except Exception as e:
                return JsonResponse({"detail": f"Invalid comment FQID: {e}"}, status=400)

            view = CommentLikesViewSet.as_view({"get": "list", "post": "create"})
            return view(
                request,
                author_serial=author_serial_path,
                entry_serial=entry_serial_path,
                comment_fqid=obj_fqid,
            )
        else:
            # ----- entry like -----
            view = EntryLikesViewSet.as_view({"get": "list", "post": "create"})
            return view(request, entry_fqid=obj_fqid)

    # -------- ENTRY (existing federated post handler) --------
    if payload_type == "":
        actor_data = (
            payload.get("actor_data")
            or payload.get("author_data")
            or payload.get("author")
        )

        if actor_data:
            serial = (
                actor_data.get("serial")
                or (actor_data.get("id").split("/")[-1] if actor_data.get("id") else None)
            )

            if serial:
                defaults = {
                    "displayName": actor_data.get("displayName", ""),
                    "github": actor_data.get("github", ""),
                    "host": actor_data.get("host", ""),
                    "profileImage": actor_data.get("profileImage", ""),
                    "description": actor_data.get("description", ""),
                    "web": actor_data.get("web", actor_data.get("url", "")),
                    "is_active": True,
                    "is_admin": False,
                    "is_approved": True,
                    "is_local": False,
                }

                created_dt = (
                    parse_datetime(actor_data.get("created"))
                    if actor_data.get("created") else None
                )
                updated_dt = (
                    parse_datetime(actor_data.get("updated"))
                    if actor_data.get("updated") else None
                )

                author_obj, created = Author.objects.update_or_create(
                    serial=serial,
                    defaults=defaults
                )

                if created_dt:
                    author_obj.created = created_dt
                if updated_dt:
                    author_obj.updated = updated_dt
                author_obj.save()

        try:
            result = entries_services.process_federated_public_post(payload)
            status_map = {
                "created": 201,
                "exists": 200,
                "updated": 200,
                "ignored": 200,
                "error": 400
            }
            status_code = status_map.get(result.get("status"), 400)
            return JsonResponse(
                {"detail": "ok", "status": result.get("status")},
                status=status_code
            )

        except Exception as e:
            return JsonResponse({"detail": f"Entry processing error: {e}"}, status=400)

    # -------- FALLBACK --------
    return JsonResponse({"detail": f"Unsupported payload type '{payload_type}'"}, status=400)

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