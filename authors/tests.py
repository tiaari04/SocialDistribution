from django.test import TestCase

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from authors.models import Author


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
        url = reverse("authors:list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "TestUser")

    def test_author_detail_view(self):
        #As an author, I have a consistent public profile page.
        url = reverse("authors:detail", args=[self.author.serial])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.author.displayName)

    def test_author_edit_requires_login(self):
        #As an author, I must log in to edit my profile.
        url = reverse("authors:edit", args=[self.author.serial])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # redirected to login

    def test_author_edit_post_updates_profile(self):
        #As an author, I can update my display name and description.
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

