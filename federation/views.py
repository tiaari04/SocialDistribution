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
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    fqid = data.get("fqid")
    author_serial = data.get("author")
    serial = data.get("serial")

    if not fqid or not author_serial:
        return JsonResponse({"error": "Missing required fields: fqid, author"}, status=400)

    try:
        author = Author.objects.get(serial=author_serial)
    except Author.DoesNotExist:
        return JsonResponse({"error": "Author not found"}, status=404)

    published_raw = data.get("published")
    if published_raw:
        published = parse_datetime(published_raw)
    else:
        published = None

    entry, created = Entry.objects.update_or_create(
        fqid=fqid,
        defaults={
            "serial": serial,
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
        entry.save()

    return JsonResponse({
        "status": "saved",
        "created": created,
        "fqid": entry.fqid,
    }, status=200)

