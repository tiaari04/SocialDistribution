from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
import json
from authors.models import Author
from entries.models import Entry
from federation.utils import check_basic_auth

@csrf_exempt
def newEntry(request):
    node = check_basic_auth(request)
    if not node:
        return JsonResponse({"error": "Unauthorized"}, status=401)

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
        author_created_dt = parse_datetime(author_data.get("created")) if author_data.get("created") else None
        author_updated_dt = parse_datetime(author_data.get("updated")) if author_data.get("updated") else None
        author_defaults = {
            "serial": author_data.get("serial", ""),
            "displayName": author_data.get("displayName", ""),
            "github": author_data.get("github", ""),
            "host": author_data.get("host", ""),
            "is_active": author_data.get("is_active", True),
            "is_admin": author_data.get("is_admin", False),
            "is_approved": author_data.get("is_approved", False),
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
        author, author_created = Author.objects.get_or_create(
            id=author_id,
            defaults={
                "serial": author_id.split("/")[-1] if "/" in author_id else author_id,
            }
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
    if published is not None or created is not None or updated is not None:
        entry.save()
    
    return JsonResponse({
        "status": "saved",
        "created": created_flag,
        "author_created": author_created,
        "fqid": entry.fqid,
    }, status=200)