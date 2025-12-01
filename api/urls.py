from django.urls import path, include
from api import views
from federation import views as federation_views
from django.http import JsonResponse 
import logging

logger = logging.getLogger(__name__)

def federation_catchall(request, *args, **kwargs):
    logger.error(f"UNKNOWN FEDERATION HIT: {request.method} {request.path}")
    return JsonResponse({"error": "Unknown endpoint", "path": request.path}, status=404)


urlpatterns = [
    path("authors/", views.api_authors_list, name="authors-list"),
    path("authors/<str:author_serial>/", views.api_author_detail, name="author-detail"),
    path("authors/<str:author_serial>/followers/", views.api_author_followers, name="author-followers"),
    path(
        "authors/<str:author_serial>/followers/<path:foreign_encoded>/",
        views.api_author_follower_detail,
        name="author-follower-detail",
    ),
    path("authors/<str:author_serial>/following/", views.api_author_following, name="author-following"),
    path(
        "authors/<str:author_serial>/following/<str:foreign_serial>/",
        views.api_author_following_detail,
        name="author-following-detail",
    ),



    path("authors/<str:author_serial>/follow_requests/", views.api_author_follow_requests, name="author-follow-requests"),

    path("authors/<str:author_serial>/inbox", views.api_author_inbox, name="author-inbox-no-slash"),
    path("authors/<str:author_serial>/inbox/", views.api_author_inbox, name="author-inbox"),
    path("authors/<str:author_serial>/entries/", views.api_author_entries, name="author-entries"),
    path("authors/<str:author_serial>/entries/<str:entry_serial>/", views.api_author_entry_detail, name="author-entry-detail"),
    path("authors/<str:author_serial>/entries/<str:entry_serial>/image/", views.api_author_entry_image, name="author-entry-image"),
    path("authors/<str:author_serial>/entries/<str:entry_serial>/image", views.api_author_entry_image, name="author-entry-image-no-lash"),
    path("authors/<str:author_serial>/liked/", views.api_author_liked, name="author-liked"),
    path("authors/<str:author_serial>/liked/<str:like_serial>/", views.api_author_liked_detail, name="author-liked-detail"),
    path("authors/<str:author_serial>/commented/", views.api_author_commented, name="author-commented"),
    path("authors/<str:author_serial>/commented/<str:comment_serial>/", views.api_author_commented_detail, name="author-commented-detail"),
    path("authors/<str:author_serial>/inbox", views.api_author_inbox, name="author-inbox-noSlash"),
    path("authors/<str:author_serial>/entries/<str:entry_serial>", views.api_author_entry_detail, name="author-entry-detail-no-slash"),
    path("authors/<str:author_serial>/entries", views.api_author_entries, name="author-entries-no-slash"),
    path("authors/<str:author_serial>", views.api_author_detail, name="author-detail-no-slash"),
    path("authors/<str:author_serial>/entries/<str:entry_serial>/images/", views.api_author_entry_image, name="author-entry-image"),
    path("authors/<str:author_serial>/entries/<str:entry_serial>/images", views.api_author_entry_image, name="author-entry-image-no-slash"),

    path("", include(("entries.api_urls", "entries"), namespace="entries-api")),
    path("authors/images/new/", federation_views.newHostedImage, name="federation-new-image"),

    # Stream & public listing
    path("stream/", views.api_stream, name="api-stream"),
    path("public/entries/", views.api_public_entries, name="api-public-entries"),

    #team skyblue
    path("reading", views.api_public_entries, name="api-reading"),

    path(r'^.*$', federation_catchall),
    ]