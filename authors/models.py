from django.db import models

class Author(models.Model):
    # The author’s globally unique URL (used across nodes)
    id = models.URLField(primary_key=True)

    # The host node this author belongs to (e.g., your server’s base URL)
    host = models.URLField()

    # Display name for the author (e.g., “Koustav Sikder”)
    displayName = models.CharField(max_length=100)

    # A short bio or “about me” description
    description = models.TextField(blank=True)

    # Optional website or personal blog
    web = models.URLField(blank=True, null=True)

    # GitHub profile link (optional)
    github = models.URLField(blank=True, null=True)

    # Profile image (as a link to an image, not a file upload)
    profileImage = models.URLField(blank=True, null=True)

    # Helper method to check if the author is local to this node
    def is_local(self):
        return "localhost" in self.host or "127.0.0.1" in self.host

    def __str__(self):
        return self.displayName
