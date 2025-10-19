from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict
from .models import Entry, Author

import json

def stream_home(request):
    return JsonResponse({"message": "Stream home endpoint (not implemented yet)"})


def public_entries(request):
    """
    Returns all public entries.
    """
    if request.method == "GET":
        entries = Entry.objects.filter(visibility=Entry.Visibility.PUBLIC).order_by("-published")
        data = [model_to_dict(e) for e in entries]
        return JsonResponse(data, safe=False)
    return HttpResponseNotAllowed(["GET"])


@csrf_exempt
def entry_create(request):
    """
    Create a new entry (POST).
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            author_id = data.get("author_id")
            author = get_object_or_404(Author, id=author_id)

            entry = Entry.objects.create(
                id=data.get("id"),
                title=data.get("title"),
                web=data.get("web"),
                description=data.get("description"),
                contentType=data.get("contentType"),
                content=data.get("content"),
                author=author,
                published=timezone.now(),
                visibility=data.get("visibility", Entry.Visibility.PUBLIC),
            )
            return JsonResponse(model_to_dict(entry), status=201)

        except Exception as e:
            return HttpResponseBadRequest(f"Error creating entry: {e}")

    return HttpResponseNotAllowed(["POST"])


def entry_detail(request, entry_serial):
    """
    Retrieve a specific entry by ID (GET).
    """
    if request.method == "GET":
        entry = get_object_or_404(Entry, id=entry_serial)
        return JsonResponse(model_to_dict(entry))
    return HttpResponseNotAllowed(["GET"])


@csrf_exempt
def entry_edit(request, entry_serial):
    """
    Edit an existing entry (PATCH/PUT).
    """
    entry = get_object_or_404(Entry, id=entry_serial)

    if request.method in ["PUT", "PATCH"]:
        try:
            data = json.loads(request.body)
            for field, value in data.items():
                if hasattr(entry, field):
                    setattr(entry, field, value)
            entry.save()
            return JsonResponse(model_to_dict(entry))
        except Exception as e:
            return HttpResponseBadRequest(f"Error updating entry: {e}")

    return HttpResponseNotAllowed(["PUT", "PATCH"])
