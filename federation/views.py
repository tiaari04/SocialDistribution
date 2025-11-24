from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
import json
from authors.models import Author
from adminpage.models import HostedImage
from entries.models import Entry, Like, Comment
from entries.services import _ensure_author

@csrf_exempt
def newEntry(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    
    try:
        data = json.loads(request.body.decode("utf-8"))
        print(data)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    

    published_raw = data.get("published")
    published = parse_datetime(published_raw) if published_raw else None
    created_raw = data.get("created")
    created = parse_datetime(created_raw) if created_raw else None
    updated_raw = data.get("updated")
    updated = parse_datetime(updated_raw) if updated_raw else None
    

    author_id = data.get("author_id")
    if not author_id:
        return JsonResponse({"error": "author_id is required"}, status=400)
    
 
    author_data = data.get("author_data")
    
    if author_data:
        print(author_data)
        author_created_dt = parse_datetime(author_data.get("created")) if author_data.get("created") else None
        author_updated_dt = parse_datetime(author_data.get("updated")) if author_data.get("updated") else None
        author_defaults = {
            "serial": author_data.get("serial", ""),
            "displayName": author_data.get("displayName", ""),
            "github": author_data.get("github", ""),
            "host": author_data.get("host", ""),
            "is_active": author_data.get("is_active", True),
            "is_admin": author_data.get("is_admin", False),
            "is_approved": author_data.get("is_approved", True),
            "is_local": False, 
            "profileImage": author_data.get("profileImage", ""),
            "description": author_data.get("description", ""),
            "web": author_data.get("web", ""),
        }
        
        author, author_created = Author.objects.update_or_create(
            id=author_id,
            defaults=author_defaults
        )
        
        if author_created_dt:
            author.created = author_created_dt
        if author_updated_dt:
            author.updated = author_updated_dt
        if author_created_dt or author_updated_dt:
            author.save()
    else:
        print("didnt find author data")
        if "/" in author_id:
            author_serial = author_id.rstrip("/").split("/")[-1]
        else:
            author_serial = author_id

        author, author_created = Author.objects.update_or_create(
            serial=author_serial,
            defaults=author_defaults
        )
    

    entry, created_flag = Entry.objects.update_or_create(
        fqid=data.get("fqid"),
        defaults={
            "serial": data.get("serial"),
            "author": author,  
            "title": data.get("title", ""),
            "web": data.get("web", ""),
            "description": data.get("description", ""),
            "content": data.get("content", ""),
            "image_url": data.get("image_url"),
            "is_local": data.get("is_local", False),
            "content_type": data.get("content_type", Entry.ContentType.PLAIN),
            "is_edited": data.get("is_edited", False),
            "likes_count": data.get("likes_count", 0),
            "visibility": data.get("visibility", Entry.Visibility.PUBLIC),
        }
    )
    
    if published is not None:
        entry.published = published
    if created is not None:
        entry.created = created
    if updated is not None:
        entry.updated = updated

    entry.save()

    return JsonResponse({
        "status": "saved",
        "created": not exists,
    }, status=200)
    
    
@csrf_exempt
def newHostedImage(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        print("INBOUND IMAGE PAYLOAD:", data)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    file_name = data.get("file_name") or data.get("filename")
    if not file_name:
        return JsonResponse(
            {"error": "file_name is required for hosted_image"}, status=400
        )

    created_raw = data.get("created")
    created_dt = parse_datetime(created_raw) if created_raw else None
    admin_uploaded = data.get("admin_uploaded", True)
    img, created = HostedImage.objects.update_or_create(
        file=file_name,
        defaults={
            "admin_uploaded": admin_uploaded,
        },
    )

    if created_dt and hasattr(img, "created_at"):
        img.created_at = created_dt
        img.save(update_fields=["created_at"])

    return JsonResponse(
        {
            "status": "saved",
            "created": created,
            "image_id": img.pk,
        },
        status=200,
    )

@csrf_exempt
def newLike(request): # works for entry likes and comment likes 
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    
    try:
        data = json.loads(request.body.decode("utf-8"))
        print(data)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    author_payload = data.get('author') or {}
    author = _ensure_author(author_payload)
    object_fqid = data.get('object_fqid')
    if not object_fqid:
        return {'status': 'error', 'error': 'missing_object'}

    if author:
        existing = Like.objects.filter(author=author, object_fqid=object_fqid).first()
        if existing:
            return JsonResponse({'status': 'exists', 'object': data.get('fqid')}, status=200)

    like = Like.objects.create(
        fqid=data.get('id') or f"{object_fqid}#like-{timezone.now().timestamp()}",
        author=author,
        object_fqid=object_fqid,
        published=data.get('published'),
    )

    return JsonResponse({
        "status": "created",
        "fqid": like.fqid,
        "object": like.object_fqid,
    }, status=201)

@csrf_exempt
def newComment(request): 
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    
    try:
        data = json.loads(request.body.decode("utf-8"))
        print(data)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    author_payload = data.get('author') or {}
    author = _ensure_author(author_payload)
    entry_fqid = data.get('entry_id')
    if not entry_fqid:
        return {'status': 'error', 'error': 'missing_entry'}
    try:
        entry = Entry.objects.get(fqid=entry_fqid)
    except Entry.DoesNotExist:
        return {'status': 'error', 'error': 'entry_not_found'}

    comment = Comment.objects.create(
        fqid=data.get('id') or f"{entry.fqid}#comment-{timezone.now().timestamp()}",
        author=author,
        entry=entry,
        content=data.get('comment') or data.get('content') or '',
        content_type=data.get('contentType') or data.get('content_type') or entry.ContentType.MARKDOWN,
        published=data.get('published') or timezone.now(),
        web=data.get('web', ''),
    )

    return JsonResponse({
        "status": "saved",
        "fqid": comment.fqid,
        "entry_fqid": entry_fqid,
    }, status=200)