from django.db import models
from django.utils import timezone
from authors.models import Author, MAX_URL, TimeStampedModel

class FollowRequest(TimeStampedModel):
    """
    Stores follow workflow between authors (local or remote).
    We use Author FKs (which are FQID PKs) to ensure global uniqueness.
    """
    actor = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="follow_requests_sent")
    author_followed = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="follow_requests_received")

    class State(models.TextChoices):
        REQUESTING = "requesting", "requesting"
        ACCEPTED = "accepted", "accepted"
        REJECTED = "rejected", "rejected"

    state = models.CharField(max_length=20, choices=State.choices, default=State.REQUESTING, db_index=True)
    published = models.DateTimeField(default=timezone.now, db_index=True)  # ordering and API visibility

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["actor", "author_followed"], name="unique_follow_request_pair"
            )
        ]
        indexes = [
            models.Index(fields=["author_followed", "state"]),
            models.Index(fields=["actor", "state"]),
            models.Index(fields=["published"]),
        ]
        ordering = ["-published", "-created"]

    def __str__(self) -> str:
        return f"{self.actor.displayName} -> {self.author_followed.displayName} ({self.state})"


class InboxItem(TimeStampedModel):
    """
    Optional convenience store for remote POSTs to /inbox so you can audit what arrived.
    For entries/comments/likes you should ALSO persist the concrete models (Entry/Comment/Like).
    """
    recipient = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="inbox_items")
    # 'entry' | 'follow' | 'like' | 'comment'
    type = models.CharField(max_length=20, db_index=True)
    object_fqid = models.URLField(max_length=MAX_URL, blank=True, help_text="FQID of the primary object, if applicable.")
    payload = models.JSONField()  # raw body you received (sanitized)
    received_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["recipient", "received_at"]),
            models.Index(fields=["type"]),
        ]
        ordering = ["-received_at", "-created"]

    def __str__(self) -> str:
        return f"InboxItem({self.type}) for {self.recipient.displayName}"
