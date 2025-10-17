from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from authors.models import Author, MAX_URL, TimeStampedModel

serial_validator = RegexValidator(
    regex=r"^(?!http)(?!.*:).+$",
    message="Serial must not start with 'http' and must not contain ':'."
)

class Entry(TimeStampedModel):
    """
    Represents a social entry/post with FQID primary key.
    """
    fqid = models.URLField(max_length=MAX_URL, primary_key=True)  # API id (FQID)
    # Optional local serial portion used in URLs like /authors/{AUTHOR_SERIAL}/entries/{ENTRY_SERIAL}
    serial = models.CharField(max_length=200, blank=True, null=True, db_index=True, validators=[serial_validator])

    title = models.CharField(max_length=300, blank=True)
    web = models.URLField(max_length=MAX_URL, blank=True)
    description = models.TextField(blank=True)
    content = models.TextField(blank=True)

    class ContentType(models.TextChoices):
        MARKDOWN = "text/markdown", "text/markdown"
        PLAIN = "text/plain", "text/plain"
        BASE64 = "application/base64", "application/base64"
        PNG = "image/png;base64", "image/png;base64"
        JPEG = "image/jpeg;base64", "image/jpeg;base64"

    content_type = models.CharField(max_length=50, choices=ContentType.choices, default=ContentType.PLAIN)

    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="entries")

    published = models.DateTimeField(default=timezone.now, db_index=True)
    # auto_now sits in TimeStampedModel.updated
    is_edited = models.BooleanField(default=False, db_index=True)

    class Visibility(models.TextChoices):
        PUBLIC = "PUBLIC", "PUBLIC"
        FRIENDS = "FRIENDS", "FRIENDS"
        UNLISTED = "UNLISTED", "UNLISTED"
        DELETED = "DELETED", "DELETED"

    visibility = models.CharField(
        max_length=20, choices=Visibility.choices, default=Visibility.PUBLIC, db_index=True
    )

    class Meta:
        indexes = [
            models.Index(fields=["serial"]),
            models.Index(fields=["published"]),
            models.Index(fields=["visibility"]),
            models.Index(fields=["author", "published"]),
        ]
        ordering = ["-published", "-created"]

    def mark_edited(self, save=True):
        self.is_edited = True
        if save:
            self.save(update_fields=["is_edited", "updated"])

    def mark_deleted(self, save=True):
        self.visibility = self.Visibility.DELETED
        if save:
            self.save(update_fields=["visibility", "updated"])

    def __str__(self) -> str:
        return self.title or self.fqid


class Comment(TimeStampedModel):
    """
    Comment with FQID PK to support remote comments.
    """
    fqid = models.URLField(max_length=MAX_URL, primary_key=True)
    author = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True, related_name="comments")
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()

    content_type = models.CharField(
        max_length=50,
        choices=Entry.ContentType.choices,
        default=Entry.ContentType.MARKDOWN,
    )
    published = models.DateTimeField(default=timezone.now, db_index=True)
    web = models.URLField(max_length=MAX_URL, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["published"]),
            models.Index(fields=["entry", "published"]),
        ]
        ordering = ["-published", "-created"]

    def __str__(self) -> str:
        return f"Comment {self.fqid}"


class Like(TimeStampedModel):
    """
    A Like object, addressable by FQID. Points at `object_fqid` (entry or comment).
    """
    fqid = models.URLField(max_length=MAX_URL, primary_key=True)
    author = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True, related_name="likes")
    object_fqid = models.URLField(max_length=MAX_URL, db_index=True)  # entry or comment FQID
    published = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["object_fqid"]),
            models.Index(fields=["published"]),
            models.Index(fields=["author", "published"]),
        ]
        ordering = ["-published", "-created"]

    def __str__(self) -> str:
        return f"Like {self.fqid}"


class EntryDelivery(TimeStampedModel):
    """
    Tracks which inboxes an entry was sent to, to support re-sends on edit/delete.
    """
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name="deliveries")
    recipient_author_fqid = models.URLField(max_length=MAX_URL, db_index=True)
    delivered_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["entry", "recipient_author_fqid"], name="unique_entry_recipient_delivery"
            )
        ]
        indexes = [
            models.Index(fields=["recipient_author_fqid", "delivered_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.entry.fqid} -> {self.recipient_author_fqid}"
