from django.test import TestCase, override_settings
from uuid import uuid4
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from authors.models import Author
from adminpage.models import HostedImage

User = get_user_model()


class AdminPageViewsTests(TestCase):
    def setUp(self):
        # Users
        self.active_user = User.objects.create_user(
            username="activeuser",
            password="pw",
            is_active=True,
        )
        self.pending_user = User.objects.create_user(
            username="pendinguser",
            password="pw",
            is_active=False,
        )

        # Authors
        self.active_author = Author.objects.create(
            id=f"http://testserver/api/authors/{uuid4().hex}",
            host="http://testserver/api/",
            displayName="Active Author",
            is_local=True,
            is_active=True,
            user=self.active_user,
        )
        self.inactive_author = Author.objects.create(
            id=f"http://elsewhere/api/authors/{uuid4().hex}",
            host="http://elsewhere/api/",
            displayName="Inactive Author",
            is_local=False,
            is_active=False,
            user=None,
        )

        # Images
        self.img1 = HostedImage.objects.create(
            # If your model uses a FileField, the "file" value is its relative path string.
            file="uploads/images/example1.png",
            alt_text="first image",
            is_public=True,
            url="http://cdn.example.com/images/example1.png",
            uploaded_by=self.active_user,
            created_at=timezone.now(),
        )
        self.img2 = HostedImage.objects.create(
            file="uploads/images/holiday_photo.jpg",
            alt_text="beach",
            is_public=False,
            url="http://cdn.example.com/images/holiday_photo.jpg",
            uploaded_by=self.active_user,
            created_at=timezone.now(),
        )

    # -------- Dashboard --------

    def test_dashboard_counts_render(self):
        url = reverse("adminpage:dashboard")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertIn("total_images", res.context)
        self.assertIn("total_authors", res.context)
        self.assertIn("pending_users", res.context)
        self.assertEqual(res.context["total_images"], 2)
        self.assertEqual(res.context["total_authors"], 1)  # only active authors
        self.assertEqual(res.context["pending_users"], 1)

    # -------- Pending Users --------

    def test_pending_users_lists_only_inactive(self):
        url = reverse("adminpage:pending-users")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        pending = list(res.context["pending"])
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].username, "pendinguser")
        self.assertFalse(pending[0].is_active)

    @override_settings(NODE_API_BASE="http://localnode/api/")
    def test_approve_user_activates_user_and_creates_author(self):
        url = reverse("adminpage:approve-user", args=[self.pending_user.id])
        res = self.client.post(url, follow=True)
        self.assertEqual(res.status_code, 200)

        # User should be active now
        self.pending_user.refresh_from_db()
        self.assertTrue(self.pending_user.is_active)

        # Author should exist (created or revived)
        author = Author.objects.filter(user=self.pending_user).first()
        self.assertIsNotNone(author)
        self.assertTrue(author.is_active)
        self.assertTrue(author.is_local)
        self.assertTrue(author.id.startswith("http://localnode/api/authors/"))

    def test_reject_user_deletes_user_and_linked_author(self):
        # Create a pending user with a linked (inactive) author record
        rejectee = User.objects.create_user(
            username="rejectme", password="pw", is_active=False
        )
        Author.objects.create(
            id=f"http://testserver/api/authors/{uuid4().hex}",
            host="http://testserver/api/",
            displayName="Reject Me",
            is_local=True,
            is_active=False,
            user=rejectee,
        )

        url = reverse("adminpage:reject-user", args=[rejectee.id])
        res = self.client.post(url, follow=True)
        self.assertEqual(res.status_code, 200)

        self.assertFalse(User.objects.filter(username="rejectme").exists())
        self.assertFalse(Author.objects.filter(displayName="Reject Me").exists())

    # -------- Authors --------

    def test_authors_list_shows_only_active_by_default_and_search(self):
        # Default: only active authors
        url = reverse("adminpage:authors")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        authors = list(res.context["authors"])
        self.assertEqual(len(authors), 1)
        self.assertEqual(authors[0].displayName, "Active Author")

        # Search matches (case-insensitive)
        res2 = self.client.get(url, {"q": "active"})
        self.assertEqual(res2.status_code, 200)
        authors2 = list(res2.context["authors"])
        self.assertEqual(len(authors2), 1)
        self.assertEqual(authors2[0].displayName, "Active Author")

        # Search miss
        res3 = self.client.get(url, {"q": "zzz"})
        self.assertEqual(res3.status_code, 200)
        self.assertEqual(list(res3.context["authors"]), [])

    def test_author_delete_soft_deactivates_author_and_user(self):
        # Link the inactive_author to a user to test user deactivation path
        linked_user = User.objects.create_user(
            username="authoruser", password="pw", is_active=True
        )
        self.inactive_author.user = linked_user
        self.inactive_author.is_active = True
        self.inactive_author.save()

        url = reverse("adminpage:author-delete", args=[self.inactive_author.pk])
        res = self.client.post(url, follow=True)
        self.assertEqual(res.status_code, 200)

        self.inactive_author.refresh_from_db()
        self.assertFalse(self.inactive_author.is_active)

        linked_user.refresh_from_db()
        self.assertFalse(linked_user.is_active)

    # -------- Images --------

    def test_images_list_renders_and_orders(self):
        url = reverse("adminpage:images")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertIn("images", res.context)
        self.assertEqual(res.context["q"], "")
        # newest first
        ids = list(res.context["images"].values_list("id", flat=True))
        self.assertEqual(ids, sorted(ids, reverse=True))

    def test_images_list_search_by_file_contains(self):
        # The view filters on file__icontains
        url = reverse("adminpage:images")
        res = self.client.get(url, {"q": "holiday"})
        self.assertEqual(res.status_code, 200)
        imgs = list(res.context["images"])
        self.assertEqual(len(imgs), 1)
        self.assertEqual(imgs[0].id, self.img2.id)

    def test_image_delete_removes_record(self):
        url = reverse("adminpage:image-delete", args=[self.img1.id])
        res = self.client.post(url, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertFalse(HostedImage.objects.filter(id=self.img1.id).exists())

    # -------- Public JSON --------

    def test_public_images_json(self):
        url = reverse("adminpage:public-images-json")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        payload = res.json()
        self.assertIn("images", payload)
        self.assertGreaterEqual(len(payload["images"]), 2)
        sample = payload["images"][0]
        self.assertIn("id", sample)
        self.assertIn("url", sample)
        self.assertIn("created_at", sample)
