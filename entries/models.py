from django.db import models
from authors.models import Author  # Import from your authors app
from django.utils import timezone


class Entry(models.Model):
    id = models.URLField(primary_key=True)
    title = models.CharField(max_length=200)
    web = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True)

    class ContentType(models.TextChoices):
        MARKDOWN = "text/markdown", "Markdown"
        PLAIN = "text/plain", "Plain text"
        PNG = "image/png;base64", "PNG Image (Base64)"
        JPEG = "image/jpeg;base64", "JPEG Image (Base64)"
        APPLICATION = "application/base64", "Other Base64"

    contentType = models.CharField(
        max_length=50,
        choices=ContentType.choices,
        default=ContentType.PLAIN,
    )

    content = models.TextField(blank=True)
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name="entries"
    )

    published = models.DateTimeField(default=timezone.now)

    class Visibility(models.TextChoices):
        PUBLIC = "PUBLIC", "Public"
        FRIENDS = "FRIENDS", "Friends Only"
        UNLISTED = "UNLISTED", "Unlisted"
        DELETED = "DELETED", "Deleted"

    visibility = models.CharField(
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.PUBLIC
    )

    def __str__(self):
        return f"{self.title} by {self.author.displayName}"


class Like(models.Model):
    id = models.URLField(primary_key=True)
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name="likes"
    )
    published = models.DateTimeField(default=timezone.now)
    object_liked = models.URLField()  # The URL of the object being liked (Entry or Comment)

    def __str__(self):
        return f"{self.author.displayName} liked {self.object_liked}"


class Comment(models.Model):
    id = models.URLField(primary_key=True)
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    comment = models.TextField()

    class ContentType(models.TextChoices):
        MARKDOWN = "text/markdown", "Markdown"
        PLAIN = "text/plain", "Plain text"

    contentType = models.CharField(
        max_length=50,
        choices=ContentType.choices,
        default=ContentType.PLAIN
    )

    published = models.DateTimeField(default=timezone.now)
    entry = models.ForeignKey(
        Entry,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    likes = models.ManyToManyField(Like, blank=True)
    web = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"Comment by {self.author.displayName} on {self.entry.title}"
