from django.urls import path
from entries import api_views

urlpatterns = [
    path(
        "authors/<str:author_serial>/entries/<str:entry_serial>/comments/",
        api_views.EntryCommentsViewSet.as_view({"get": "list", "post": "create"}),
        name="api-entry-comments",
    ),
    path(
        "authors/<str:author_serial>/entries/<str:entry_serial>/likes/",
        api_views.EntryLikesViewSet.as_view({"get": "list", "post": "create"}),
        name="api-entry-likes",
    ),

    # FQID based endpoints
    path(
        "entries/<path:entry_fqid>/comments/",
        api_views.EntryCommentsViewSet.as_view({"get": "list", "post": "create"}),
        name="api-entry-comments-fqid",
    ),
    path(
        "entries/<path:entry_fqid>/likes/",
        api_views.EntryLikesViewSet.as_view({"get": "list", "post": "create"}),
        name="api-entry-likes-fqid",
    ),
    path(
        "entries/<path:entry_fqid>/comments/<path:comment_fqid>/likes/",
        api_views.CommentLikesViewSet.as_view({"get": "list", "post": "create"}),
        name="api-entry-comment-likes",
    ),

    # comment likes
    path(
        "authors/<str:author_serial>/entries/<str:entry_serial>/comments/<path:comment_fqid>/likes/",
        api_views.CommentLikesViewSet.as_view({"get": "list", "post": "create"}),
        name="api-entry-comment-likes",
    ),
]
