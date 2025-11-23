from django.urls import path
from . import views
from . import federation_views

app_name = "adminpage"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    # Images
    path("images/", views.images_list, name="images"),
    path("images/upload/", views.image_upload, name="image-upload"),
    path("images/<int:pk>/delete/", views.image_delete, name="image-delete"),
    path("images/<int:pk>/send/", federation_views.send_image_to_nodes, name="image-send"),

    # Authors (URL PKs!)
    path("authors/", views.authors_list, name="authors"),
    path("authors/new/", views.author_create, name="author-create"),
    path("authors/<path:pk>/edit/", views.author_update, name="author-update"),
    path("authors/<path:pk>/delete/", views.author_delete, name="author-delete"),
    path("authors/<path:pk>/<str:tab>/", views.author_detail, name="author-detail-tab"),

    # Approvals (Users are still int PKs)
    path("approvals/", views.pending_users, name="pending-users"),
    path('approvals/<path:user_id>/approve/', views.approve_user, name='approve-user'),

    # Federation Management
    path("federation/", federation_views.federation_dashboard, name="federation-dashboard"),
    path("federation/nodes/", federation_views.nodes_list, name="federation-nodes"),
    path("federation/nodes/new/", federation_views.node_create, name="federation-node-create"),
    path("federation/nodes/<int:pk>/", federation_views.node_detail, name="federation-node-detail"),
    path("federation/nodes/<int:pk>/edit/", federation_views.node_update, name="federation-node-update"),
    path("federation/nodes/<int:pk>/delete/", federation_views.node_delete, name="federation-node-delete"),
    path("federation/nodes/<int:pk>/toggle/", federation_views.node_toggle_active, name="federation-node-toggle"),
    path("federation/nodes/<int:pk>/test/", federation_views.node_test_connection, name="federation-node-test"),
    path("federation/logs/", federation_views.logs_list, name="federation-logs"),

]
