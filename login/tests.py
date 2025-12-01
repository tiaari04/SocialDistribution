from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from authors.models import Author
from adminpage.models import HostedImage

import builtins


class AuthViewTests(TestCase):
    def setUp(self):
        # Patch print so we can suppress ONLY the "Error getting domain" noise
        self._original_print = builtins.print

        def filtered_print(*args, **kwargs):
            if args and isinstance(args[0], str):
                first = args[0].strip()
                if first.startswith("Error getting domain"):
                    # swallow this one line in tests
                    return
            # otherwise behave normally
            self._original_print(*args, **kwargs)

        builtins.print = filtered_print

        # normal setup
        self.client = Client()
        self.signup_url = reverse("login:signup")
        self.login_url = reverse("login:login")
        self.await_approval_url = reverse("login:await_approval")

    def tearDown(self):
        # restore original print so other tests / code are unaffected
        builtins.print = self._original_print

    def test_signup_creates_author_and_user(self):
        print("\n[START] test_signup_creates_author_and_user — ensures signup creates User + Author")

        data = {
            "username": "testuser",
            "password1": "123passWordddd123",
            "password2": "123passWordddd123",
            "githubLink": "",
            "web": "",
            "description": "",
        }
        response = self.client.post(self.signup_url, data)
        self.assertEqual(response.status_code, 200)

        self.assertTrue(User.objects.filter(username="testuser").exists())
        user = User.objects.get(username="testuser")

        self.assertTrue(Author.objects.filter(user=user).exists())

        print("[END] test_signup_creates_author_and_user — Passed")

    def test_signup_password_mismatch_does_not_create_user_or_author(self):
        print("\n[START] test_signup_password_mismatch_does_not_create_user_or_author — ensures bad passwords do not create user")

        data = {
            "username": "baduser",
            "password1": "Password12345!",
            "password2": "DifferentPassword123!",
            "githubLink": "",
            "web": "",
            "description": "",
        }
        response = self.client.post(self.signup_url, data)
        self.assertEqual(response.status_code, 200)  # form re-rendered with errors

        self.assertFalse(User.objects.filter(username="baduser").exists())
        self.assertFalse(Author.objects.filter(displayName="baduser").exists())

        print("[END] test_signup_password_mismatch_does_not_create_user_or_author — Passed")

    def test_signup_uses_default_profile_image_when_no_file_uploaded(self):
        print("\n[START] test_signup_uses_default_profile_image_when_no_file_uploaded — checks fallback profile image")

        data = {
            "username": "nodefaultimageuser",
            "password1": "StrongPass!234",
            "password2": "StrongPass!234",
            "githubLink": "",
            "web": "",
            "description": "User with no profile image",
        }
        response = self.client.post(self.signup_url, data)
        self.assertEqual(response.status_code, 200)

        user = User.objects.get(username="nodefaultimageuser")
        author = Author.objects.get(user=user)

        self.assertEqual(
            author.profileImage,
            "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_640.png",
        )

        print("[END] test_signup_uses_default_profile_image_when_no_file_uploaded — Passed")

    def test_login_with_valid_credentials_and_approved_active_author_redirects_to_stream_home(self):
        print("\n[START] test_login_with_valid_credentials_and_approved_active_author_redirects_to_stream_home — checks redirect to stream")

        user = User.objects.create_user(username="approveduser", password="StrongPass!234")
        author = Author.objects.create(
            id="http://testserver/authors/serial-approved",
            user=user,
            host="http://testserver/api/",
            displayName="approveduser",
            github="",
            profileImage="http://example.com/avatar.png",
            web="",
            description="",
            is_local=True,
            serial="serial-approved",
            is_admin=False,
            is_approved=True,
            is_active=True,
        )

        response = self.client.post(self.login_url, {
            "username": "approveduser",
            "password": "StrongPass!234",
        })
        expected_url = reverse("entries:stream_home", kwargs={"author_serial": author.serial})

        self.assertRedirects(response, expected_url)

        print("[END] test_login_with_valid_credentials_and_approved_active_author_redirects_to_stream_home — Passed")

    def test_login_with_admin_redirects_to_admin_dashboard(self):
        print("\n[START] test_login_with_admin_redirects_to_admin_dashboard — checks admin redirect")

        user = User.objects.create_user(username="adminuser", password="StrongPass!234")
        Author.objects.create(
            id="http://testserver/authors/serial-admin",
            user=user,
            host="http://testserver/api/",
            displayName="adminuser",
            github="",
            profileImage="http://example.com/admin.png",
            web="",
            description="",
            is_local=True,
            serial="serial-admin",
            is_admin=True,
            is_approved=True,
            is_active=True,
        )

        response = self.client.post(self.login_url, {
            "username": "adminuser",
            "password": "StrongPass!234",
        })
        expected_url = reverse("adminpage:dashboard")

        self.assertRedirects(response, expected_url)

        print("[END] test_login_with_admin_redirects_to_admin_dashboard — Passed")

    def test_login_unapproved_author_redirects_to_await_approval(self):
        print("\n[START] test_login_unapproved_author_redirects_to_await_approval — checks redirect to waiting page")

        user = User.objects.create_user(username="pendinguser", password="StrongPass!234")
        Author.objects.create(
            id="http://testserver/authors/serial-pending",
            user=user,
            host="http://testserver/api/",
            displayName="pendinguser",
            github="",
            profileImage="http://example.com/pending.png",
            web="",
            description="",
            is_local=True,
            serial="serial-pending",
            is_admin=False,
            is_approved=False,
            is_active=True,
        )

        response = self.client.post(self.login_url, {
            "username": "pendinguser",
            "password": "StrongPass!234",
        })
        expected_url = self.await_approval_url

        self.assertRedirects(response, expected_url)

        print("[END] test_login_unapproved_author_redirects_to_await_approval — Passed")

    def test_login_with_valid_user_but_missing_author_redirects_back_to_login(self):
        print("\n[START] test_login_with_valid_user_but_missing_author_redirects_back_to_login — user has no author")

        User.objects.create_user(username="nouserauthor", password="StrongPass!234")

        response = self.client.post(self.login_url, {
            "username": "nouserauthor",
            "password": "StrongPass!234",
        })

        self.assertRedirects(response, self.login_url)

        print("[END] test_login_with_valid_user_but_missing_author_redirects_back_to_login — Passed")

    def test_login_with_invalid_credentials_redirects_back_to_login(self):
        print("\n[START] test_login_with_invalid_credentials_redirects_back_to_login — wrong password test")

        User.objects.create_user(username="someuser", password="CorrectPassword123!")

        response = self.client.post(self.login_url, {
            "username": "someuser",
            "password": "WrongPassword999!",
        })

        self.assertRedirects(response, self.login_url)

        print("[END] test_login_with_invalid_credentials_redirects_back_to_login — Passed")