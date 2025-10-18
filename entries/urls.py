from django.urls import path
from entries import views
from entries import api_views

urlpatterns = [
    path("", views.stream_home, name="home"),  
    path("public/", views.public_entries, name="public"),
    path("create/", views.entry_create, name="create"),  
    path("entries/<str:entry_serial>/", views.entry_detail, name="entry-detail"),
    path("entries/<str:entry_serial>/edit/", views.entry_edit, name="entry-edit"),
    # Comments & Likes API (author-serial + entry-serial forms)
    path("api/authors/<str:author_serial>/entries/<str:entry_serial>/comments/", api_views.EntryCommentsViewSet.as_view({'get': 'list', 'post': 'create'}), name="api-entry-comments"),
    path("api/authors/<str:author_serial>/entries/<str:entry_serial>/likes/", api_views.EntryLikesViewSet.as_view({'get': 'list', 'post': 'create'}), name="api-entry-likes"),
    # FQID based endpoints
    path("api/entries/<path:entry_fqid>/comments/", api_views.EntryCommentsViewSet.as_view({'get': 'list', 'post': 'create'}), name="api-entry-comments-fqid"),
    path("api/entries/<path:entry_fqid>/likes/", api_views.EntryLikesViewSet.as_view({'get': 'list', 'post': 'create'}), name="api-entry-likes-fqid"),
]