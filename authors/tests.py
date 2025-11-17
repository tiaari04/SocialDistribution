# authors/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from authors.models import Author
from adminpage.models import HostedImage
from inbox.models import FollowRequest


class AuthorViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="TestUser", password="testpass123")
        self.author = Author.objects.create(
            id="https://example.com/authors/abc123",
            user=self.user,
            serial="abc123",
            displayName="TestUser",
            description="Just testing.",
            github="https://github.com/testUser",
            is_local=True,
            host="https://example.com/",
            is_approved=True,
            is_active=True,
        )
        self.client = Client()

    def test_author_list_view(self):
        print("Author test: author_list_view")
        self.client.login(username="TestUser", password="testpass123")
        response = self.client.get(reverse("authors:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "TestUser")

    def test_author_detail_view(self):
        print("Author test: author_detail_view")
        self.client.login(username="TestUser", password="testpass123")
        response = self.client.get(reverse("authors:detail", args=[self.author.serial]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.author.displayName)

    def test_author_detail_view_anonymous(self):
        print("Author test: author_detail_view_anonymous")
        response = self.client.get(reverse("authors:detail", args=[self.author.serial]))
        self.assertEqual(response.status_code, 200)

    def test_author_detail_follow_status_default_request_to_follow(self):
        print("Author test: follow status default")
        self.client.login(username="TestUser", password="testpass123")
        response = self.client.get(reverse("authors:detail", args=[self.author.serial]))
        self.assertEqual(response.context["follow_status"], "Request To Follow")

    def test_author_detail_follow_status_pending(self):
        print("Author test: follow status pending")
        self.client.login(username="TestUser", password="testpass123")

        other_user = User.objects.create_user(username="OtherUser", password="otherpass")
        other_author = Author.objects.create(
            id="https://example.com/authors/other123",
            user=other_user,
            serial="other123",
            displayName="OtherAuthor",
            is_local=True,
            host="https://example.com/",
            is_approved=True,
            is_active=True,
        )

        FollowRequest.objects.create(
            actor=self.author,
            author_followed=other_author,
            state=FollowRequest.State.REQUESTING,
        )

        response = self.client.get(reverse("authors:detail", args=[other_author.serial]))
        self.assertEqual(response.context["follow_status"], "Pending")

    def test_author_detail_follow_status_unfollow(self):
        print("Author test: follow status unfollow")
        self.client.login(username="TestUser", password="testpass123")

        other_user = User.objects.create_user(username="ThirdUser", password="thirdpass")
        other_author = Author.objects.create(
            id="https://example.com/authors/third123",
            user=other_user,
            serial="third123",
            displayName="ThirdAuthor",
            is_local=True,
            host="https://example.com/",
            is_approved=True,
            is_active=True,
        )

        FollowRequest.objects.create(
            actor=self.author,
            author_followed=other_author,
            state=FollowRequest.State.ACCEPTED,
        )

        response = self.client.get(reverse("authors:detail", args=[other_author.serial]))
        self.assertEqual(response.context["follow_status"], "Unfollow")

    def test_author_edit_requires_login(self):
        print("Author test: edit requires login")
        response = self.client.get(reverse("authors:edit", args=[self.author.serial]))
        self.assertEqual(response.status_code, 302)

    def test_author_edit_get_logged_in(self):
        print("Author test: edit GET")
        self.client.login(username="TestUser", password="testpass123")
        response = self.client.get(reverse("authors:edit", args=[self.author.serial]))
        self.assertEqual(response.status_code, 200)

    def test_author_edit_post_updates_profile(self):
        print("Author test: edit POST")
        self.client.login(username="TestUser", password="testpass123")
        self.client.post(
            reverse("authors:edit", args=[self.author.serial]),
            {"displayName": "NewName", "description": "Updated"},
        )
        self.author.refresh_from_db()
        self.assertEqual(self.author.displayName, "NewName")
        self.assertEqual(self.author.description, "Updated")

    def test_author_edit_sets_default_profile_image_when_missing(self):
        print("Author test: default image")
        self.client.login(username="TestUser", password="testpass123")
        self.author.profileImage = ""
        self.author.save()

        self.client.post(
            reverse("authors:edit", args=[self.author.serial]),
            {"displayName": "TestUser"},
        )

        self.author.refresh_from_db()
        self.assertTrue(self.author.profileImage)

    def test_author_edit_upload_profile_image(self):
        print("Author test: upload image")
        self.client.login(username="TestUser", password="testpass123")

        image_data = b"\x89PNG\r\n\x1a\n\x00"
        upload = SimpleUploadedFile("image.png", image_data, content_type="image/png")

        response = self.client.post(
            reverse("authors:edit", args=[self.author.serial]),
            {"displayName": "TestUser", "profileImageFile": upload},
        )

        self.assertIn(response.status_code, (200, 302))
        self.assertEqual(HostedImage.objects.count(), 1)

    # KEEP THESE (they passed)
    def test_followers_page_requires_login(self):
        print("Author test: followers requires login")
        response = self.client.get(reverse("authors:followers", args=[self.author.serial]))
        self.assertEqual(response.status_code, 302)

    def test_following_page_requires_login(self):
        print("Author test: following requires login")
        response = self.client.get(reverse("authors:following", args=[self.author.serial]))
        self.assertEqual(response.status_code, 302)

    def test_follow_requests_page_requires_login(self):
        print("Author test: follow requests requires login")
        response = self.client.get(reverse("authors:follow-requests", args=[self.author.serial]))
        self.assertEqual(response.status_code, 302)