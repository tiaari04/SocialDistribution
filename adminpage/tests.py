from django.test import TestCase, override_settings
from django.urls import reverse, NoReverseMatch
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from uuid import uuid4

from authors.models import Author
from adminpage.models import HostedImage

User = get_user_model()


@override_settings(
    DEFAULT_FILE_STORAGE="django.core.files.storage.FileSystemStorage",
)
class AdminPageSmokeTests(TestCase):
    def setUp(self):
        self.active_user = User.objects.create_user(
            username="active",
            password="pw",
            is_active=True,
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(self.active_user)

        self.pending_user = User.objects.create_user(
            username="pending",
            password="pw",
            is_active=False,
        )

        self.active_author = Author.objects.create(
            id=f"http://testserver/api/authors/{uuid4().hex}",
            host="http://testserver/api/",
            displayName="Active Admin Author",
            is_local=True,
            is_active=True,
            is_admin=True, 
            user=self.active_user,
        )
        self.img = HostedImage.objects.create(
            file=ContentFile(b"fake-bytes", name="example.png")
        )

    def test_dashboard_loads(self):
        res = self.client.get(reverse("adminpage:dashboard"))
        self.assertEqual(res.status_code, 200)

    def test_pending_users_loads(self):
        res = self.client.get(reverse("adminpage:pending-users"))
        self.assertEqual(res.status_code, 200)

    @override_settings(NODE_API_BASE="http://localnode/api/")
    def test_approve_user_basic(self):
        res = self.client.post(reverse("adminpage:approve-user", args=[self.pending_user.id]), follow=True)
        self.assertEqual(res.status_code, 200)
        self.pending_user.refresh_from_db()
        self.assertTrue(self.pending_user.is_active)

    def test_authors_list_loads(self):
        res = self.client.get(reverse("adminpage:authors"))
        self.assertEqual(res.status_code, 200)

    def test_images_list_loads(self):
        res = self.client.get(reverse("adminpage:images"))
        self.assertEqual(res.status_code, 200)

    def test_image_delete_basic(self):
        res = self.client.post(reverse("adminpage:image-delete", args=[self.img.id]), follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertFalse(HostedImage.objects.filter(id=self.img.id).exists())

    def test_public_images_json_ok(self):
        try:
            url = reverse("adminpage:public-images-json")
        except NoReverseMatch:
            self.skipTest("Route 'adminpage:public-images-json' not defined")
            return
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertIn("images", res.json())