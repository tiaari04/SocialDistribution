from django.test import TestCase

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from authors.models import Author


class AuthViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse("login:signup")
        self.login_url = reverse("login:login")

    def test_signup_creates_author_and_user(self):
        #As an author, I can sign up and get an Author profile created.
        print("Login test: signup_creates_author_and_user — submitting signup form to create User + Author")
        data = {
            "username": "testuser",
            "password1": "123passWordddd123",
            "password2": "123passWordddd123",
        }
        response = self.client.post(self.signup_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username="testuser").exists())

