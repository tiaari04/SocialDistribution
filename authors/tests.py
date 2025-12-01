# authors/tests.py
import json
from unittest.mock import patch

from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from authors.models import Author
from adminpage.models import HostedImage
from inbox.models import FollowRequest
from authors.views import author_inbox


class AuthorModelTests(TestCase):
    """
    Tests focused on the Author model itself (is_friend, __str__, etc.).
    """

    def setUp(self):
        self.author_a = Author.objects.create(
            id="https://example.com/authors/a",
            serial="a",
            displayName="Author A",
            is_local=True,
            host="https://example.com/",
            is_approved=True,
            is_active=True,
        )
        self.author_b = Author.objects.create(
            id="https://example.com/authors/b",
            serial="b",
            displayName="Author B",
            is_local=True,
            host="https://example.com/",
            is_approved=True,
            is_active=True,
        )

    def test_author_str_representation(self):
        desc = "Author __str__ includes displayName and id"
        print(f"[START] {desc}")
        s = str(self.author_a)
        self.assertIn("Author A", s)
        self.assertIn("https://example.com/authors/a", s)
        print(f"[END] {desc} — Passed")

    def test_is_friend_same_author_true(self):
        desc = "is_friend returns True when comparing an author to themselves"
        print(f"[START] {desc}")
        self.assertTrue(self.author_a.is_friend(self.author_a))
        print(f"[END] {desc} — Passed")

    def test_is_friend_mutual_follow_accepted_true(self):
        desc = "is_friend returns True for mutual accepted follows"
        print(f"[START] {desc}")
        FollowRequest.objects.create(
            actor=self.author_a,
            author_followed=self.author_b,
            state=FollowRequest.State.ACCEPTED,
        )
        FollowRequest.objects.create(
            actor=self.author_b,
            author_followed=self.author_a,
            state=FollowRequest.State.ACCEPTED,
        )
        self.assertTrue(self.author_a.is_friend(self.author_b))
        self.assertTrue(self.author_b.is_friend(self.author_a))
        print(f"[END] {desc} — Passed")

    def test_is_friend_one_way_follow_false(self):
        desc = "is_friend returns False when follow is only one-way"
        print(f"[START] {desc}")
        FollowRequest.objects.create(
            actor=self.author_a,
            author_followed=self.author_b,
            state=FollowRequest.State.ACCEPTED,
        )
        self.assertFalse(self.author_a.is_friend(self.author_b))
        self.assertFalse(self.author_b.is_friend(self.author_a))
        print(f"[END] {desc} — Passed")


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

    # ----------------------
    # author_list
    # ----------------------

    def test_author_list_requires_login(self):
        desc = "author_list requires login"
        print(f"[START] {desc}")
        response = self.client.get(reverse("authors:list"))
        self.assertEqual(response.status_code, 302)
        print(f"[END] {desc} — Passed")

    def test_author_list_view(self):
        desc = "author_list loads and displays authors"
        print(f"[START] {desc}")
        self.client.login(username="TestUser", password="testpass123")
        response = self.client.get(reverse("authors:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "TestUser")
        self.assertIn("authors", response.context)
        print(f"[END] {desc} — Passed")

    # ----------------------
    # author_detail
    # ----------------------

    def test_author_detail_view(self):
        desc = "author_detail loads correctly"
        print(f"[START] {desc}")
        self.client.login(username="TestUser", password="testpass123")
        response = self.client.get(reverse("authors:detail", args=[self.author.serial]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.author.displayName)
        print(f"[END] {desc} — Passed")

    def test_author_detail_view_anonymous(self):
        desc = "author_detail loads for anonymous user"
        print(f"[START] {desc}")
        response = self.client.get(reverse("authors:detail", args=[self.author.serial]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("follow_status", response.context)
        print(f"[END] {desc} — Passed")

    def test_author_detail_follow_status_default_request_to_follow(self):
        desc = "default follow_status is 'Request To Follow'"
        print(f"[START] {desc}")
        self.client.login(username="TestUser", password="testpass123")
        response = self.client.get(reverse("authors:detail", args=[self.author.serial]))
        self.assertEqual(response.context["follow_status"], "Request To Follow")
        print(f"[END] {desc} — Passed")

    def test_author_detail_follow_status_pending(self):
        desc = "follow_status becomes 'Pending' when request exists"
        print(f"[START] {desc}")
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
        print(f"[END] {desc} — Passed")

    def test_author_detail_follow_status_unfollow(self):
        desc = "follow_status becomes 'Unfollow' when accepted"
        print(f"[START] {desc}")
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
        print(f"[END] {desc} — Passed")

    def test_author_detail_follow_status_when_other_follows_me_only(self):
        desc = "follow_status remains 'Request To Follow' when other follows me only"
        print(f"[START] {desc}")
        self.client.login(username="TestUser", password="testpass123")

        other_user = User.objects.create_user(username="FollowerOnly", password="fpass")
        other_author = Author.objects.create(
            id="https://example.com/authors/followeronly",
            user=other_user,
            serial="followeronly",
            displayName="FollowerOnly",
            is_local=True,
            host="https://example.com/",
            is_approved=True,
            is_active=True,
        )

        # Only other_author -> self.author
        FollowRequest.objects.create(
            actor=other_author,
            author_followed=self.author,
            state=FollowRequest.State.ACCEPTED,
        )

        response = self.client.get(reverse("authors:detail", args=[other_author.serial]))
        self.assertEqual(response.context["follow_status"], "Request To Follow")
        print(f"[END] {desc} — Passed")

    def test_author_detail_follower_and_request_counts(self):
        desc = "author_detail shows correct follower and pending counts"
        print(f"[START] {desc}")
        self.client.login(username="TestUser", password="testpass123")

        # Accepted
        follower_user = User.objects.create_user(username="FollowerUser", password="p1")
        follower_author = Author.objects.create(
            id="https://example.com/authors/follower",
            user=follower_user,
            serial="follower",
            displayName="Follower",
            is_local=True,
            host="https://example.com/",
            is_approved=True,
            is_active=True,
        )
        FollowRequest.objects.create(
            actor=follower_author,
            author_followed=self.author,
            state=FollowRequest.State.ACCEPTED,
        )

        # Pending
        pending_user = User.objects.create_user(username="PendingUser", password="p2")
        pending_author = Author.objects.create(
            id="https://example.com/authors/pending",
            user=pending_user,
            serial="pending",
            displayName="Pending",
            is_local=True,
            host="https://example.com/",
            is_approved=True,
            is_active=True,
        )
        FollowRequest.objects.create(
            actor=pending_author,
            author_followed=self.author,
            state=FollowRequest.State.REQUESTING,
        )

        response = self.client.get(reverse("authors:detail", args=[self.author.serial]))
        self.assertEqual(response.context["follower_count"], 1)
        print(f"[END] {desc} — Passed")

    # ----------------------
    # author_edit
    # ----------------------

    def test_author_edit_requires_login(self):
        desc = "author_edit requires login"
        print(f"[START] {desc}")
        response = self.client.get(reverse("authors:edit", args=[self.author.serial]))
        self.assertEqual(response.status_code, 302)
        print(f"[END] {desc} — Passed")

    def test_author_edit_get_logged_in(self):
        desc = "author_edit GET loads properly"
        print(f"[START] {desc}")
        self.client.login(username="TestUser", password="testpass123")
        response = self.client.get(reverse("authors:edit", args=[self.author.serial]))
        self.assertEqual(response.status_code, 200)
        print(f"[END] {desc} — Passed")

    def test_author_edit_post_updates_profile(self):
        desc = "author_edit POST updates profile fields"
        print(f"[START] {desc}")
        self.client.login(username="TestUser", password="testpass123")
        self.client.post(
            reverse("authors:edit", args=[self.author.serial]),
            {"displayName": "NewName", "description": "Updated"},
        )
        self.author.refresh_from_db()
        self.assertEqual(self.author.displayName, "NewName")
        self.assertEqual(self.author.description, "Updated")
        print(f"[END] {desc} — Passed")

    def test_author_edit_sets_default_profile_image_when_missing(self):
        desc = "author_edit sets default profileImage when missing"
        print(f"[START] {desc}")
        self.client.login(username="TestUser", password="testpass123")
        self.author.profileImage = ""
        self.author.save()

        self.client.post(
            reverse("authors:edit", args=[self.author.serial]),
            {"displayName": "TestUser"},
        )

        self.author.refresh_from_db()
        self.assertTrue(self.author.profileImage)
        print(f"[END] {desc} — Passed")

    def test_author_edit_upload_profile_image(self):
        desc = "author_edit saves uploaded profileImage"
        print(f"[START] {desc}")
        self.client.login(username="TestUser", password="testpass123")

        image_data = b"\x89PNG\r\n\x1a\n\x00"
        upload = SimpleUploadedFile("image.png", image_data, content_type="image/png")

        response = self.client.post(
            reverse("authors:edit", args=[self.author.serial]),
            {"displayName": "TestUser", "profileImageFile": upload},
        )

        self.assertIn(response.status_code, (200, 302))
        self.assertEqual(HostedImage.objects.count(), 1)
        print(f"[END] {desc} — Passed")

    # ----------------------
    # followers / following / follow_requests pages
    # ----------------------

    def test_followers_page_requires_login(self):
        desc = "followers page requires login"
        print(f"[START] {desc}")
        response = self.client.get(reverse("authors:followers", args=[self.author.serial]))
        self.assertEqual(response.status_code, 302)
        print(f"[END] {desc} — Passed")

    def test_following_page_requires_login(self):
        desc = "following page requires login"
        print(f"[START] {desc}")
        response = self.client.get(reverse("authors:following", args=[self.author.serial]))
        self.assertEqual(response.status_code, 302)
        print(f"[END] {desc} — Passed")

    def test_follow_requests_page_requires_login(self):
        desc = "follow_requests page requires login"
        print(f"[START] {desc}")
        response = self.client.get(reverse("authors:follow-requests", args=[self.author.serial]))
        self.assertEqual(response.status_code, 302)
        print(f"[END] {desc} — Passed")

    def test_followers_page_classifies_friends_and_followers(self):
        desc = "followers page splits mutual friends and one-way followers"
        print(f"[START] {desc}")
        self.client.login(username="TestUser", password="testpass123")

        # Friend (mutual)
        friend_user = User.objects.create_user(username="FriendUser", password="pass1")
        friend_author = Author.objects.create(
            id="https://example.com/authors/friend",
            user=friend_user,
            serial="friend",
            displayName="Friend",
            is_local=True,
            host="https://example.com/",
            is_approved=True,
            is_active=True,
        )
        FollowRequest.objects.create(
            actor=friend_author,
            author_followed=self.author,
            state=FollowRequest.State.ACCEPTED,
        )
        FollowRequest.objects.create(
            actor=self.author,
            author_followed=friend_author,
            state=FollowRequest.State.ACCEPTED,
        )

        # One-way follower
        follower_user = User.objects.create_user(username="FollowerUser2", password="pass2")
        follower_author = Author.objects.create(
            id="https://example.com/authors/follower2",
            user=follower_user,
            serial="follower2",
            displayName="Follower2",
            is_local=True,
            host="https://example.com/",
            is_approved=True,
            is_active=True,
        )
        FollowRequest.objects.create(
            actor=follower_author,
            author_followed=self.author,
            state=FollowRequest.State.ACCEPTED,
        )

        response = self.client.get(reverse("authors:followers", args=[self.author.serial]))
        friends = response.context["friends"]
        followers = response.context["followers"]

        self.assertEqual(len(friends), 1)
        self.assertEqual(friends[0].actor, friend_author)

        self.assertEqual(len(followers), 1)
        self.assertEqual(followers[0].actor, follower_author)

        print(f"[END] {desc} — Passed")

    def test_following_page_shows_only_accepted_outgoing(self):
        desc = "following page shows only accepted outgoing relations"
        print(f"[START] {desc}")
        self.client.login(username="TestUser", password="testpass123")

        # Accepted follow
        target_user = User.objects.create_user(username="TargetUser", password="pass")
        target_author = Author.objects.create(
            id="https://example.com/authors/target",
            user=target_user,
            serial="target",
            displayName="Target",
            is_local=True,
            host="https://example.com/",
            is_approved=True,
            is_active=True,
        )
        FollowRequest.objects.create(
            actor=self.author,
            author_followed=target_author,
            state=FollowRequest.State.ACCEPTED,
        )

        # Pending follow
        pending_user = User.objects.create_user(username="PendingOut", password="pass2")
        pending_author = Author.objects.create(
            id="https://example.com/authors/pendingout",
            user=pending_user,
            serial="pendingout",
            displayName="PendingOut",
            is_local=True,
            host="https://example.com/",
            is_approved=True,
            is_active=True,
        )
        FollowRequest.objects.create(
            actor=self.author,
            author_followed=pending_author,
            state=FollowRequest.State.REQUESTING,
        )

        response = self.client.get(reverse("authors:following", args=[self.author.serial]))
        following_list = response.context["following_list"]
        self.assertEqual(len(following_list), 1)
        self.assertEqual(following_list[0].author_followed, target_author)

        print(f"[END] {desc} — Passed")

    def test_follow_requests_page_shows_only_pending_incoming(self):
        desc = "follow_requests page shows only pending incoming requests"
        print(f"[START] {desc}")
        self.client.login(username="TestUser", password="testpass123")

        # Pending incoming
        pending_user = User.objects.create_user(username="PendingIn", password="pass")
        pending_author = Author.objects.create(
            id="https://example.com/authors/pendingin",
            user=pending_user,
            serial="pendingin",
            displayName="PendingIn",
            is_local=True,
            host="https://example.com/",
            is_approved=True,
            is_active=True,
        )
        FollowRequest.objects.create(
            actor=pending_author,
            author_followed=self.author,
            state=FollowRequest.State.REQUESTING,
        )

        # Accepted incoming (should NOT show)
        accepted_user = User.objects.create_user(username="AcceptedIn", password="pass2")
        accepted_author = Author.objects.create(
            id="https://example.com/authors/acceptedin",
            user=accepted_user,
            serial="acceptedin",
            displayName="AcceptedIn",
            is_local=True,
            host="https://example.com/",
            is_approved=True,
            is_active=True,
        )
        FollowRequest.objects.create(
            actor=accepted_author,
            author_followed=self.author,
            state=FollowRequest.State.ACCEPTED,
        )

        response = self.client.get(reverse("authors:follow-requests", args=[self.author.serial]))
        requests = response.context["requests"]

        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].actor, pending_author)

        print(f"[END] {desc} — Passed")


class AuthorInboxTests(TestCase):
    """
    Tests for the author_inbox view (POST-only, JSON handling, and response mapping).
    """

    def setUp(self):
        self.factory = RequestFactory()
        self.author_serial = "inbox-tester"

    def test_author_inbox_rejects_non_post(self):
        desc = "author_inbox rejects non-POST methods"
        print(f"[START] {desc}")
        request = self.factory.get(f"/authors/{self.author_serial}/inbox")
        response = author_inbox(request, self.author_serial)
        self.assertEqual(response.status_code, 405)
        print(f"[END] {desc} — Passed")

    def test_author_inbox_invalid_json_returns_400(self):
        desc = "author_inbox returns 400 for invalid JSON"
        print(f"[START] {desc}")
        request = self.factory.post(
            f"/authors/{self.author_serial}/inbox",
            data="not-json",
            content_type="application/json",
        )
        response = author_inbox(request, self.author_serial)
        self.assertEqual(response.status_code, 400)
        print(f"[END] {desc} — Passed")

    @patch("authors.views.entries_services.process_inbox_for")
    def test_author_inbox_created_status_201(self, mock_process):
        desc = "author_inbox returns 201 when entry is created"
        print(f"[START] {desc}")
        mock_process.return_value = {"status": "created"}
        payload = {"type": "Note"}

        request = self.factory.post(
            f"/authors/{self.author_serial}/inbox",
            data=json.dumps(payload),
            content_type="application/json",
        )
        response = author_inbox(request, self.author_serial)

        self.assertEqual(response.status_code, 201)
        print(f"[END] {desc} — Passed")

    @patch("authors.views.entries_services.process_inbox_for")
    def test_author_inbox_exists_status_201(self, mock_process):
        desc = "author_inbox returns 201 when entry already exists"
        print(f"[START] {desc}")
        mock_process.return_value = {"status": "exists"}
        payload = {"type": "Note"}

        request = self.factory.post(
            f"/authors/{self.author_serial}/inbox",
            data=json.dumps(payload),
            content_type="application/json",
        )
        response = author_inbox(request, self.author_serial)

        self.assertEqual(response.status_code, 201)
        print(f"[END] {desc} — Passed")

    @patch("authors.views.entries_services.process_inbox_for")
    def test_author_inbox_ignored_status_200(self, mock_process):
        desc = "author_inbox returns 200 when entry is ignored"
        print(f"[START] {desc}")
        mock_process.return_value = {"status": "ignored"}
        payload = {"type": "Note"}

        request = self.factory.post(
            f"/authors/{self.author_serial}/inbox",
            data=json.dumps(payload),
            content_type="application/json",
        )
        response = author_inbox(request, self.author_serial)

        self.assertEqual(response.status_code, 200)
        print(f"[END] {desc} — Passed")

    @patch("authors.views.entries_services.process_inbox_for")
    def test_author_inbox_error_status_400(self, mock_process):
        desc = "author_inbox returns 400 when service returns error"
        print(f"[START] {desc}")
        mock_process.return_value = {"status": "error", "error": "something went wrong"}
        payload = {"type": "Note"}

        request = self.factory.post(
            f"/authors/{self.author_serial}/inbox",
            data=json.dumps(payload),
            content_type="application/json",
        )
        response = author_inbox(request, self.author_serial)

        self.assertEqual(response.status_code, 400)
        print(f"[END] {desc} — Passed")
