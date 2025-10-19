from django.urls import path
from entries import views

urlpatterns = [
    path("", views.stream_home, name="home"),
    path("public/", views.public_entries, name="public"),
    path("create/", views.entry_create, name="create"),
    path("entries/<str:entry_serial>/", views.entry_detail, name="entry-detail"),
    path("entries/<str:entry_serial>/edit/", views.entry_edit, name="entry-edit"),
]