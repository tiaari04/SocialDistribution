from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
import json
from authors.models import Author
from entries.models import Entry

@csrf_exempt
def newEntry(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    
    try:
        data = json.loads(request.body.decode("utf-8"))
        print(data)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    # Parse datetime fields
    published_raw = data.get("published")
    published = parse_datetime(published_raw) if published_raw else None
    
    created_raw = data.get("created")
    created = parse_datetime(created_raw) if created_raw else None
    
    updated_raw = data.get("updated")
    updated = parse_datetime(updated_raw) if updated_raw else None
    
    # Handle the author as a string ID
    author_id = data.get("author_id")
    
    # Create or update the entry
    entry, created_flag = Entry.objects.update_or_create(
        fqid=data.get("fqid"),
        defaults={
            "serial": data.get("serial"),
            "author_id": author_id,
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
    
    # Set timestamp fields separately if provided
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
        "fqid": entry.fqid,
    }, status=200)