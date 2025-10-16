from django.contrib import admin
from .models import Entry, Comment, Like, EntryDelivery

@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "visibility", "published", "is_edited")
    list_filter = ("visibility", "is_edited", "content_type")
    search_fields = ("title", "fqid", "description", "author__displayName")
    date_hierarchy = "published"
    ordering = ("-published",)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("fqid", "entry", "author", "published")
    list_filter = ("content_type",)
    search_fields = ("fqid", "entry__fqid", "author__displayName", "content")
    date_hierarchy = "published"

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("fqid", "author", "object_fqid", "published")
    search_fields = ("fqid", "author__displayName", "object_fqid")
    date_hierarchy = "published"

@admin.register(EntryDelivery)
class EntryDeliveryAdmin(admin.ModelAdmin):
    list_display = ("entry", "recipient_author_fqid", "delivered_at")
    search_fields = ("entry__fqid", "recipient_author_fqid")
    date_hierarchy = "delivered_at"
