from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
import json
from authors.models import Author
from adminpage.models import HostedImage
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
    
    
@csrf_exempt
def newHostedImage(request):
    """
    Receive a hosted image from another node and store it so it shows up
    in adminpage/images_list.

    Expects JSON like:
      {
        "type": "hosted_image",
        "file_name": "uploads/images/abcd1234.png",
        "url": "https://remote-storage/.../abcd1234.png",   # optional
        "created": "2025-11-23T00:12:34Z",
        "admin_uploaded": true
      }
    """
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

    # De-duplicate by file name: if the same image is sent again, just update flags
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