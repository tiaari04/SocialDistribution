from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from uuid import uuid4

from authors.models import Author
from adminpage.models import HostedImage

User = get_user_model()


class AdminPageSmokeTests(TestCase):
    def setUp(self):
        # Minimal fixtures
        self.active_user = User.objects.create_user("active", password="pw", is_active=True)
        self.pending_user = User.objects.create_user("pending", password="pw", is_active=False)

        self.active_author = Author.objects.create(
            id=f"http://testserver/api/authors/{uuid4().hex}",
            host="http://testserver/api/",
            displayName="Active Author",
            is_local=True,
            is_active=True,
            user=self.active_user,
        )

        self.img = HostedImage.objects.create(
            file="uploads/images/example.png",
            alt_text="example",
            is_public=True,
            url="http://cdn.example.com/images/example.png",
            uploaded_by=self.active_user,
            created_at=timezone.now(),
        )

    # -------- Dashboard (loads) --------
    def test_dashboard_loads(self):
        res = self.client.get(reverse("adminpage:dashboard"))
        self.assertEqual(res.status_code, 200)

    # -------- Pending users (lists) --------
    def test_pending_users_loads(self):
        res = self.client.get(reverse("adminpage:pending-users"))
        self.assertEqual(res.status_code, 200)

    # -------- Approve user (activates + creates author) --------
    @override_settings(NODE_API_BASE="http://localnode/api/")
    def test_approve_user_basic(self):
        res = self.client.post(reverse("adminpage:approve-user", args=[self.pending_user.id]), follow=True)
        self.assertEqual(res.status_code, 200)
        self.pending_user.refresh_from_db()
        self.assertTrue(self.pending_user.is_active)

    # -------- Authors list (basic render) --------
    def test_authors_list_loads(self):
        res = self.client.get(reverse("adminpage:authors"))
        self.assertEqual(res.status_code, 200)

    # -------- Image list + delete (basic paths) --------
    def test_images_list_loads(self):
        res = self.client.get(reverse("adminpage:images"))
        self.assertEqual(res.status_code, 200)

    def test_image_delete_basic(self):
        res = self.client.post(reverse("adminpage:image-delete", args=[self.img.id]), follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertFalse(HostedImage.objects.filter(id=self.img.id).exists())

    # -------- Public JSON (shape exists) --------
    def test_public_images_json_ok(self):
        res = self.client.get(reverse("adminpage:public-images-json"))
        self.assertEqual(res.status_code, 200)
        self.assertIn("images", res.json())