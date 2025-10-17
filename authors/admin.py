from django.contrib import admin
from .models import Author

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("displayName", "is_local", "host", "id")
    list_filter = ("is_local",)
    search_fields = ("displayName", "id", "host", "github", "web")
