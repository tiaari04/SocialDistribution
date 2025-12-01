from django.urls import path
from django.contrib.auth import views as auth_views
from authors import views


urlpatterns = [
    path("", views.author_list, name="list"),  
    path("<str:author_serial>/", views.author_detail, name="detail"),  
    path("<str:author_serial>/edit/", views.author_edit, name="edit"),  
    path("<str:author_serial>/entries/", views.author_entries_page, name="entries"),  
    path("<str:author_serial>/followers/", views.author_followers_page, name="followers"),
    path("<str:author_serial>/following/", views.author_following_page, name="following"),
    path("<str:author_serial>/follow-requests/", views.follow_requests_page, name="follow-requests"),
    path("<str:author_serial>/inbox/", views.author_inbox, name="author-inbox"),

    path("<str:author_serial>", views.author_detail, name="detail-no-slash"), 
]