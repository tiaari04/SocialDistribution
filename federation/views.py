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

    # Parse the published datetime
    published_raw = data.get("published")
    published = parse_datetime(published_raw) if published_raw else None

    # Handle the author as a URL string
    author_url = data.get("author_id")


    # Create or update the entry
    entry, created = Entry.objects.update_or_create(
        fqid=data.get("fqid"),
        defaults={
            "serial": data.get("serial"),
            "author": author_url,
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
        entry.save()

    return JsonResponse({
        "status": "saved",
        "created": created,
        "fqid": entry.fqid,
    }, status=200)
