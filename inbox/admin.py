from django.contrib import admin
from .models import FollowRequest, InboxItem

@admin.register(FollowRequest)
class FollowRequestAdmin(admin.ModelAdmin):
    list_display = ("actor", "author_followed", "state", "published")
    list_filter = ("state",)
    search_fields = ("actor__displayName", "actor__id", "author_followed__displayName", "author_followed__id")
    date_hierarchy = "published"

@admin.register(InboxItem)
class InboxItemAdmin(admin.ModelAdmin):
    list_display = ("recipient", "type", "object_fqid", "received_at")
    list_filter = ("type",)
    search_fields = ("recipient__displayName", "object_fqid")
    date_hierarchy = "received_at"
