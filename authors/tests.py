from django.test import TestCase

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from authors.models import Author
from django.core.files.uploadedfile import SimpleUploadedFile
from adminpage.models import HostedImage


class AuthorViewsTest(TestCase):
    def setUp(self):
        # Create a test user and author
        self.user = User.objects.create_user(username="TestUser", password="testpass123")
        self.author = Author.objects.create(
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
        #As a node admin, I can see multiple authors on my node.
        print("Author test: author_list_view — As a node admin, I can see multiple authors on my node.")
        self.client.login(username="TestUser", password="testpass123")
        url = reverse("authors:list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "TestUser")

    def test_author_detail_view(self):
        #As an author, I have a consistent public profile page.
        print("Author test: author_detail_view — Author detail page should contain the display name.")
        self.client.login(username="TestUser", password="testpass123")
        url = reverse("authors:detail", args=[self.author.serial])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.author.displayName)

    def test_author_edit_requires_login(self):
        #As an author, I must log in to edit my profile.
        print("Author test: author_edit_requires_login — Editing an author profile requires login.")
        url = reverse("authors:edit", args=[self.author.serial])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # redirected to login

    def test_author_edit_post_updates_profile(self):
        #As an author, I can update my display name and description.
        print("Author test: author_edit_post_updates_profile — POST updates the author's profile fields.")
        self.client.login(username="TestUser", password="testpass123")
        url = reverse("authors:edit", args=[self.author.serial])
        data = {
            "displayName": "Test User Updated",
            "description": "New bio text",
            "github": "https://github.com/updated",
            "web": "https://testUser.me",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.author.refresh_from_db()
        self.assertEqual(self.author.displayName, "Test User Updated")
        self.assertEqual(self.author.description, "New bio text")

    def test_author_edit_upload_profile_image(self):
        # Uploading a profile image should create a HostedImage and set Author.profileImage
        print("Author test: author_edit_upload_profile_image — Uploading a profile image updates Author.profileImage.")
        self.client.login(username="TestUser", password="testpass123")
        url = reverse("authors:edit", args=[self.author.serial])

        # Minimal PNG header bytes for a tiny valid image
        png_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
            b"\x00\x00\x00\x0cIDATx\x9cc``\x00\x00\x00\x02\x00\x01\xe2!\xbc\x33\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        upload = SimpleUploadedFile("avatar.png", png_bytes, content_type="image/png")

        # Include the uploaded file in the POST data so the test client encodes it as multipart
        response = self.client.post(url, {"displayName": "TestUser", "profileImageFile": upload}, follow=False)
        # Should redirect to detail on success
        self.assertIn(response.status_code, (302, 200))

        # HostedImage created and Author.profileImage updated
        self.assertEqual(HostedImage.objects.count(), 1)
        hosted = HostedImage.objects.first()

        self.author.refresh_from_db()
        self.assertTrue(self.author.profileImage)
        self.assertIn(hosted.file.url, self.author.profileImage)

