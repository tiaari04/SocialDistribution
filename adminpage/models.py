# adminpage/models.py
import os
from uuid import uuid4
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_IMAGE_BYTES = 8 * 1024 * 1024  # 8 MB


def validate_image_file(f):
    ext = os.path.splitext(f.name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTS:
        raise ValidationError("Unsupported image type. Use JPG/PNG/GIF/WEBP.")
    if f.size and f.size > MAX_IMAGE_BYTES:
        raise ValidationError("Image too large (max 8 MB).")


def image_upload_to(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"uploads/images/{uuid4().hex}{ext}"


class HostedImage(models.Model):
    """
    Stores a single uploaded image that is always public.
    Intended for reuse in CommonMark posts by all users.
    """

    file = models.ImageField(upload_to=image_upload_to, validators=[validate_image_file])
    uploaded_by = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="uploaded_images",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return os.path.basename(self.file.name)

    @property
    def url(self):
        """Return the fully qualified URL from the storage backend (Cloudinary)."""
        return self.file.url
