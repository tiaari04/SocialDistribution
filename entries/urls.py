from django.urls import path
from entries import views

app_name = "entries"

urlpatterns = [
    path("stream/<str:author_serial>/", views.stream_home, name="stream_home"),
    path("public/", views.public_entries, name="public"),

    path("authors/<str:author_serial>/entries/create/", views.entry_create, name="create"),
    path("authors/<str:author_serial>/entries/<str:entry_serial>/", views.entry_detail, name="detail"),
    path("authors/<str:author_serial>/entries/<str:entry_serial>/edit/", views.entry_edit, name="edit"),
    path("authors/<str:author_serial>/entries/<str:entry_serial>/delete/", views.entry_delete, name="entry_delete"),
    path("authors/<str:author_serial>/images/pick/", views.admin_image_picker, name="admin_image_picker"),
    
    # GitHub webhook endpoint
    path("github/webhook/", views.github_webhook, name="github_webhook"),
]
