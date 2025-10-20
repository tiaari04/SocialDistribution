from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User

MAX_URL = 1024

serial_validator = RegexValidator(
    regex=r"^(?!http)(?!.*:).+$",
    message="Serial must not start with 'http' and must not contain ':'."
)

class TimeStampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    updated = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True


class Author(TimeStampedModel):
    """
    API identity is the fully-qualified URL (FQID). This is the PK to avoid collisions.
    """
    id = models.URLField(max_length=MAX_URL, primary_key=True)  # FQID
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    host = models.URLField(max_length=MAX_URL, help_text="Full API base, e.g., https://node/api/")
    displayName = models.CharField(max_length=200, db_index=True)
    github = models.URLField(max_length=MAX_URL, blank=True)
    profileImage = models.URLField(max_length=MAX_URL, blank=True)
    web = models.URLField(max_length=MAX_URL, blank=True)
    description = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False, db_index=True)
    # Convenience: whether this author account is hosted locally on this node
    is_local = models.BooleanField(default=True, db_index=True)

    # Optional: a locally convenient serial (NOT used for relations between nodes)
    serial = models.CharField(
        max_length=200, blank=True, null=True, validators=[serial_validator], db_index=True
    )

    class Meta:
        indexes = [
            models.Index(fields=["displayName"]),
            models.Index(fields=["host"]),
            models.Index(fields=["is_local"]),
            models.Index(fields=["serial"]),
        ]

    def __str__(self) -> str:
        return f"{self.displayName} ({self.id})"

    def is_friend(self, other: "Author") -> bool:
        """
        Returns True if `self` and `other` have mutually accepted follow requests.
        This relies on the `FollowRequest` model in the `inbox` app.
        """
        try:
            from inbox.models import FollowRequest
        except Exception:
            return False

        if self.id == other.id:
            return True

        # accepted follow where self -> other and other -> self
        accepted = FollowRequest.State.ACCEPTED
        return (
            FollowRequest.objects.filter(actor=self, author_followed=other, state=accepted).exists()
            and FollowRequest.objects.filter(actor=other, author_followed=self, state=accepted).exists()
        )
