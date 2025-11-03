from django.urls import path
from . import views

app_name = "adminpage"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    # Images
    path("images/", views.images_list, name="images"),
    path("images/upload/", views.image_upload, name="image-upload"),
    path("images/<int:pk>/delete/", views.image_delete, name="image-delete"),

    # Authors (URL PKs!)
    path("authors/", views.authors_list, name="authors"),
    path("authors/new/", views.author_create, name="author-create"),
    path("authors/<path:pk>/edit/", views.author_update, name="author-update"),
    path("authors/<path:pk>/delete/", views.author_delete, name="author-delete"),
    path("authors/<path:pk>/<str:tab>/", views.author_detail, name="author-detail-tab"),

    # Approvals (Users are still int PKs)
    path("approvals/", views.pending_users, name="pending-users"),
    path('approvals/<path:user_id>/approve/', views.approve_user, name='approve-user'),

]
