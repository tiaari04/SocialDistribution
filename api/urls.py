from django.urls import path, re_path
from api import views

urlpatterns = [
    # Authors
    path("authors/", views.api_authors_list, name="authors-list"),                     
    path("authors/<str:author_serial>/", views.api_author_detail, name="author-detail"), 
    path("authors/<str:author_serial>/followers/", views.api_author_followers, name="author-followers"),
    path("authors/<str:author_serial>/followers/<path:foreign_encoded>/", views.api_author_follower_detail, name="author-follower-detail"),

    path("authors/<str:author_serial>/inbox/", views.api_author_inbox, name="author-inbox"),  

    # Entries
    path("authors/<str:author_serial>/entries/", views.api_author_entries, name="author-entries"),             
    path("authors/<str:author_serial>/entries/<str:entry_serial>/", views.api_author_entry_detail, name="author-entry-detail"),
    path("authors/<str:author_serial>/entries/<str:entry_serial>/image/", views.api_author_entry_image, name="author-entry-image"),
    path("entries/<path:entry_fqid>/", views.api_entry_by_fqid, name="entry-by-fqid"),
    path("entries/<path:entry_fqid>/image/", views.api_entry_image, name="entry-image"),

    # Comments & Likes
    path("authors/<str:author_serial>/entries/<str:entry_serial>/comments/", views.api_entry_comments, name="entry-comments"),
    path("authors/<str:author_serial>/entries/<str:entry_serial>/likes/", views.api_entry_likes, name="entry-likes"),

    # ENTRY FQID based endpoints 
    path("entries/<path:entry_fqid>/comments/", views.api_entry_comments_by_fqid, name="entry-by-fqid-comments"),
    path("entries/<path:entry_fqid>/likes/", views.api_entry_likes_by_fqid, name="entry-by-fqid-likes"),

    # Liked / Commented lists
    path("authors/<str:author_serial>/liked/", views.api_author_liked, name="author-liked"),
    path("authors/<str:author_serial>/commented/", views.api_author_commented, name="author-commented"),

    # Comment detail (remote-comment FQID can be percent-encoded in URL) and likes-on-comment
    path("authors/<str:author_serial>/entries/<str:entry_serial>/comments/<path:comment_fqid>/", views.api_entry_comment_detail, name="entry-comment-detail"),
    path("authors/<str:author_serial>/entries/<str:entry_serial>/comments/<path:comment_fqid>/likes/", views.api_entry_comment_likes, name="entry-comment-likes"),

    # singular alias (spec examples sometimes use `comment` instead of `comments`)
    path("authors/<str:author_serial>/entries/<str:entry_serial>/comment/<path:comment_fqid>/", views.api_entry_comment_detail, name="entry-comment-detail-singular"),

    # Global FQID endpoints for comment/like lookups
    path("commented/<path:comment_fqid>/", views.api_comment_by_fqid, name="comment-by-fqid"),
    path("liked/<path:like_fqid>/", views.api_like_by_fqid, name="like-by-fqid"),

    # Author by FQID (remote author lookup by percent-encoded FQID)
    path("authors/<path:author_fqid>/", views.api_author_by_fqid, name="author-by-fqid"),

    # Author-by-FQID liked/commented lists (local lookups by remote author URL)
    path("authors/<path:author_fqid>/liked/", views.api_author_by_fqid_liked, name="author-by-fqid-liked"),
    path("authors/<path:author_fqid>/commented/", views.api_author_by_fqid_commented, name="author-by-fqid-commented"),

    # Per-author single liked/commented item endpoints
    path("authors/<str:author_serial>/liked/<str:like_serial>/", views.api_author_liked_detail, name="author-liked-detail"),
    path("authors/<str:author_serial>/commented/<str:comment_serial>/", views.api_author_commented_detail, name="author-commented-detail"),

    # Stream & public listing
    path("stream/", views.api_stream, name="api-stream"),
    path("public/entries/", views.api_public_entries, name="api-public-entries"),
]