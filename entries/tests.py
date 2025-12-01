from django.test import TestCase, Client
from authors.models import Author
from .models import Entry, Comment, Like, EntryDelivery
from inbox.models import FollowRequest
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import IntegrityError


class CommentsLikesTests(TestCase):
    def setUp(self):
        self.a1 = Author.objects.create(id='http://local/api/authors/1', serial='1', displayName='A1')
        self.a2 = Author.objects.create(id='http://local/api/authors/2', serial='2', displayName='A2')

        self.entry_public = Entry.objects.create(
            fqid='http://local/api/authors/2/entries/10',
            serial='10',
            author=self.a2,
            content='hello',
            visibility=Entry.Visibility.PUBLIC,
            published=timezone.now(),
        )
        self.entry_friends = Entry.objects.create(
            fqid='http://local/api/authors/2/entries/11',
            serial='11',
            author=self.a2,
            content='friends only',
            visibility=Entry.Visibility.FRIENDS,
            published=timezone.now(),
        )
        self.entry_unlisted = Entry.objects.create(
            fqid='http://local/api/authors/2/entries/12',
            serial='12',
            author=self.a2,
            content='unlisted',
            visibility=Entry.Visibility.UNLISTED,
            published=timezone.now(),
        )

        EntryDelivery.objects.create(entry=self.entry_unlisted, recipient_author_fqid=self.a1.id)
        self.client = Client()

    def test_comment_public(self):
        print("\n[START] comment_public")
        payload = {'comment': 'nice', 'id': 'http://remote/comment/1'}
        resp = self.client.post(
            '/api/authors/2/entries/10/comments/',
            data=payload,
            content_type='application/json',
            **{'HTTP_X_AUTHOR_ID': self.a1.id},
        )
        self.assertEqual(resp.status_code, 201)
        print("[END] comment_public Passed")

    def test_like_public(self):
        print("\n[START] like_public")
        resp = self.client.post(
            '/api/authors/2/entries/10/likes/',
            data={},
            content_type='application/json',
            **{'HTTP_X_AUTHOR_ID': self.a1.id},
        )
        self.assertEqual(resp.status_code, 201)
        print("[END] like_public Passed")

    def test_like_duplicate_idempotent(self):
        print("\n[START] like_duplicate_idempotent")
        resp1 = self.client.post(
            '/api/authors/2/entries/10/likes/',
            data={},
            content_type='application/json',
            **{'HTTP_X_AUTHOR_ID': self.a1.id},
        )
        self.assertEqual(resp1.status_code, 201)

        resp2 = self.client.post(
            '/api/authors/2/entries/10/likes/',
            data={},
            content_type='application/json',
            **{'HTTP_X_AUTHOR_ID': self.a1.id},
        )
        self.assertIn(resp2.status_code, (200, 201))
        print("[END] like_duplicate_idempotent Passed")

    def test_comment_friends_visibility(self):
        print("\n[START] comment_friends_visibility")
        resp = self.client.post(
            '/api/authors/2/entries/11/comments/',
            data={'comment': 'hi'},
            content_type='application/json',
            **{'HTTP_X_AUTHOR_ID': self.a1.id},
        )
        self.assertEqual(resp.status_code, 403)
        print("[END] comment_friends_visibility Passed")

    def test_comment_friends_visibility_allows_friend(self):
        print("\n[START] comment_friends_visibility_allows_friend")
        FollowRequest.objects.create(actor=self.a1, author_followed=self.a2, state=FollowRequest.State.ACCEPTED)
        FollowRequest.objects.create(actor=self.a2, author_followed=self.a1, state=FollowRequest.State.ACCEPTED)

        resp = self.client.post(
            '/api/authors/2/entries/11/comments/',
            data={'comment': 'friend comment'},
            content_type='application/json',
            **{'HTTP_X_AUTHOR_ID': self.a1.id},
        )
        self.assertEqual(resp.status_code, 201)
        print("[END] comment_friends_visibility_allows_friend Passed")

    def test_comment_unlisted_only_recipient(self):
        print("\n[START] comment_unlisted_only_recipient")
        resp = self.client.post(
            '/api/authors/2/entries/12/comments/',
            data={'comment': 'secret'},
            content_type='application/json',
            **{'HTTP_X_AUTHOR_ID': self.a1.id},
        )
        self.assertEqual(resp.status_code, 201)
        print("[END] comment_unlisted_only_recipient Passed")

    def test_comment_unlisted_forbidden_for_non_recipient(self):
        print("\n[START] comment_unlisted_forbidden_for_non_recipient")
        a3 = Author.objects.create(id='http://local/api/authors/3', serial='3', displayName='A3')
        resp = self.client.post(
            '/api/authors/2/entries/12/comments/',
            data={'comment': 'nope'},
            content_type='application/json',
            **{'HTTP_X_AUTHOR_ID': a3.id},
        )
        self.assertEqual(resp.status_code, 403)
        print("[END] comment_unlisted_forbidden_for_non_recipient Passed")

    def test_unlisted_like_allowed_for_recipient(self):
        print("\n[START] unlisted_like_allowed_for_recipient")
        resp = self.client.post(
            '/api/authors/2/entries/12/likes/',
            data={},
            content_type='application/json',
            **{'HTTP_X_AUTHOR_ID': self.a1.id},
        )
        self.assertEqual(resp.status_code, 201)
        print("[END] unlisted_like_allowed_for_recipient Passed")

    def test_unlisted_like_forbidden_for_non_recipient(self):
        print("\n[START] unlisted_like_forbidden_for_non_recipient")
        a3 = Author.objects.create(id='http://local/api/authors/3', serial='3', displayName='A3')
        resp = self.client.post(
            '/api/authors/2/entries/12/likes/',
            data={},
            content_type='application/json',
            **{'HTTP_X_AUTHOR_ID': a3.id},
        )
        self.assertEqual(resp.status_code, 403)
        print("[END] unlisted_like_forbidden_for_non_recipient Passed")

    def test_like_signals_increment_and_decrement_entry(self):
        print("\n[START] like_signals_increment_and_decrement_entry")
        self.entry_public.refresh_from_db()
        self.assertEqual(self.entry_public.likes_count, 0)

        like = Like.objects.create(
            fqid='http://local/api/likes/1',
            author=self.a1,
            object_fqid=self.entry_public.fqid,
            published=timezone.now(),
        )
        self.entry_public.refresh_from_db()
        self.assertEqual(self.entry_public.likes_count, 1)

        like.delete()
        self.entry_public.refresh_from_db()
        self.assertEqual(self.entry_public.likes_count, 0)
        print("[END] like_signals_increment_and_decrement_entry Passed")

    def test_like_signals_increment_and_decrement_comment(self):
        print("\n[START] like_signals_increment_and_decrement_comment")
        comment = Comment.objects.create(
            fqid='http://local/api/comments/1',
            author=self.a1,
            entry=self.entry_public,
            content='nice',
        )
        like = Like.objects.create(
            fqid='http://local/api/likes/2',
            author=self.a1,
            object_fqid=comment.fqid,
            published=timezone.now(),
        )
        comment.refresh_from_db()
        self.assertEqual(comment.likes_count, 1)

        like.delete()
        comment.refresh_from_db()
        self.assertEqual(comment.likes_count, 0)
        print("[END] like_signals_increment_and_decrement_comment Passed")

    def test_unique_like_constraint_enforced(self):
        print("\n[START] unique_like_constraint_enforced")
        Like.objects.create(
            fqid='http://local/api/likes/3',
            author=self.a1,
            object_fqid=self.entry_public.fqid,
            published=timezone.now(),
        )
        with self.assertRaises(IntegrityError):
            Like.objects.create(
                fqid='http://local/api/likes/4',
                author=self.a1,
                object_fqid=self.entry_public.fqid,
                published=timezone.now(),
            )
        print("[END] unique_like_constraint_enforced Passed")

    def test_friends_like_forbidden_when_not_friends(self):
        print("\n[START] friends_like_forbidden_when_not_friends")
        resp = self.client.post(
            '/api/authors/2/entries/11/likes/',
            data={},
            content_type='application/json',
            **{'HTTP_X_AUTHOR_ID': self.a1.id},
        )
        self.assertEqual(resp.status_code, 403)
        print("[END] friends_like_forbidden_when_not_friends Passed")

    def test_friends_like_allowed_for_mutual_followers(self):
        print("\n[START] friends_like_allowed_for_mutual_followers")
        FollowRequest.objects.create(actor=self.a1, author_followed=self.a2, state=FollowRequest.State.ACCEPTED)
        FollowRequest.objects.create(actor=self.a2, author_followed=self.a1, state=FollowRequest.State.ACCEPTED)
        resp = self.client.post(
            '/api/authors/2/entries/11/likes/',
            data={},
            content_type='application/json',
            **{'HTTP_X_AUTHOR_ID': self.a1.id},
        )
        self.assertEqual(resp.status_code, 201)
        print("[END] friends_like_allowed_for_mutual_followers Passed")

    def test_same_author_can_like_entry_and_comment_separately(self):
        print("\n[START] same_author_can_like_entry_and_comment_separately")
        comment = Comment.objects.create(
            fqid='http://local/api/comments/2',
            author=self.a1,
            entry=self.entry_public,
            content='comment here',
        )
        like_entry = Like.objects.create(
            fqid='http://local/api/likes/5',
            author=self.a1,
            object_fqid=self.entry_public.fqid,
            published=timezone.now(),
        )
        like_comment = Like.objects.create(
            fqid='http://local/api/likes/6',
            author=self.a1,
            object_fqid=comment.fqid,
            published=timezone.now(),
        )
        self.assertIsNotNone(like_entry.pk)
        self.assertIsNotNone(like_comment.pk)
        print("[END] same_author_can_like_entry_and_comment_separately Passed")


class EntryViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.client = Client()
        self.client.login(username="testuser", password="password")

        self.author = Author.objects.create(
            id=f"http://testserver/api/authors/{self.user.username}",
            user=self.user,
            displayName="Test Author",
            host="http://localhost",
        )
        self.author.serial = "testauthor"
        self.author.save()

        self.entry = Entry.objects.create(
            author=self.author,
            serial="testentry",
            fqid=f"{self.author.host}/authors/{self.author.serial}/entries/testentry",
            title="Initial Post",
            content="Initial content",
            content_type="text/plain",
            visibility=Entry.Visibility.PUBLIC,
            published=timezone.now(),
        )

    def test_create_entry(self):
        print("\n[START] create_entry")
        url = reverse("entries:create", kwargs={"author_serial": self.author.serial})
        data = {
            "title": "New Post",
            "content": "New content",
            "content_type": "text/plain",
            "visibility": Entry.Visibility.PUBLIC,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Entry.objects.filter(title="New Post", author=self.author).exists())
        print("[END] create_entry Passed")

    def test_edit_entry(self):
        print("\n[START] edit_entry")
        url = reverse(
            "entries:edit",
            kwargs={"author_serial": self.author.serial, "entry_serial": self.entry.serial},
        )
        data = {
            "title": "Edited Post",
            "content": "Edited content",
            "content_type": "text/plain",
            "visibility": Entry.Visibility.PUBLIC,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        self.entry.refresh_from_db()
        self.assertEqual(self.entry.title, "Edited Post")
        self.assertEqual(self.entry.content, "Edited content")
        print("[END] edit_entry Passed")

    def test_delete_entry(self):
        print("\n[START] delete_entry")
        url = reverse(
            "entries:entry_delete",
            kwargs={"author_serial": self.author.serial, "entry_serial": self.entry.serial},
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.visibility, Entry.Visibility.DELETED)
        print("[END] delete_entry Passed")

    def test_create_entry_requires_login(self):
        print("\n[START] create_entry_requires_login")
        self.client.logout()
        url = reverse("entries:create", kwargs={"author_serial": self.author.serial})
        data = {
            "title": "Anon Post",
            "content": "Should not be created",
            "content_type": "text/plain",
            "visibility": Entry.Visibility.PUBLIC,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Entry.objects.filter(title="Anon Post", author=self.author).exists())
        print("[END] create_entry_requires_login Passed")

    def test_edit_entry_requires_login(self):
        print("\n[START] edit_entry_requires_login")
        self.client.logout()
        url = reverse(
            "entries:edit",
            kwargs={"author_serial": self.author.serial, "entry_serial": self.entry.serial},
        )
        data = {
            "title": "Edited While Logged Out",
            "content": "Nope",
            "content_type": "text/plain",
            "visibility": Entry.Visibility.PUBLIC,
        }
        response = self.client.post(url, data)
        self.entry.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(self.entry.title, "Edited While Logged Out")
        print("[END] edit_entry_requires_login Passed")

    def test_non_owner_cannot_edit_entry(self):
        print("\n[START] non_owner_cannot_edit_entry")
        other_user = User.objects.create_user(username="otheruser", password="password")
        other_author = Author.objects.create(
            id=f"http://testserver/api/authors/{other_user.username}",
            user=other_user,
            displayName="Other Author",
            host="http://localhost",
            serial="otherauthor",
        )

        self.client.logout()
        self.client.login(username="otheruser", password="password")

        url = reverse(
            "entries:edit",
            kwargs={"author_serial": self.author.serial, "entry_serial": self.entry.serial},
        )
        data = {
            "title": "Malicious Edit",
            "content": "Hacked",
            "content_type": "text/plain",
            "visibility": Entry.Visibility.PUBLIC,
        }
        response = self.client.post(url, data)
        self.entry.refresh_from_db()

        self.assertIn(response.status_code, (403, 404))
        self.assertNotEqual(self.entry.title, "Malicious Edit")
        print("[END] non_owner_cannot_edit_entry Passed")


class EntryDetailVisibilityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="pass")
        self.user2 = User.objects.create_user(username="user2", password="pass")

        self.a1 = Author.objects.create(
            id=f"http://testserver/api/authors/{self.user1.username}",
            user=self.user1,
            serial="a1",
        )
        self.a2 = Author.objects.create(
            id=f"http://testserver/api/authors/{self.user2.username}",
            user=self.user2,
            serial="a2",
        )

        self.public_entry = Entry.objects.create(
            author=self.a2,
            serial="public1",
            fqid='fqid-public1',
            visibility=Entry.Visibility.PUBLIC,
            content="public post",
        )
        self.unlisted_entry = Entry.objects.create(
            author=self.a2,
            serial="unlisted1",
            fqid='fqid-unlisted1',
            visibility=Entry.Visibility.UNLISTED,
            content="unlisted post",
        )
        self.friends_entry = Entry.objects.create(
            author=self.a2,
            serial="friends1",
            fqid='fqid-friends1',
            visibility=Entry.Visibility.FRIENDS,
            content="friends post",
        )
        self.deleted_entry = Entry.objects.create(
            author=self.a2,
            serial="deleted1",
            fqid='fqid-deleted1',
            visibility=Entry.Visibility.DELETED,
            content="deleted post",
        )

    def test_public_visible_to_anyone(self):
        print("\n[START] public_visible_to_anyone")
        url = reverse("entries:detail", kwargs={"author_serial": self.a2.serial, "entry_serial": self.public_entry.serial})
        response = self.client.get(url)
        self.assertContains(response, "public post")
        print("[END] public_visible_to_anyone Passed")

    def test_unlisted_visible_even_when_logged_out(self):
        print("\n[START] unlisted_visible_even_when_logged_out")
        url = reverse("entries:detail", kwargs={"author_serial": self.a2.serial, "entry_serial": self.unlisted_entry.serial})
        response = self.client.get(url)
        self.assertContains(response, "unlisted post")
        print("[END] unlisted_visible_even_when_logged_out Passed")

    def test_friends_hidden_when_not_logged_in(self):
        print("\n[START] friends_hidden_when_not_logged_in")
        url = reverse("entries:detail", kwargs={"author_serial": self.a2.serial, "entry_serial": self.friends_entry.serial})
        response = self.client.get(url)
        if response.status_code == 200:
            self.assertNotContains(response, "friends post")
        print("[END] friends_hidden_when_not_logged_in Passed")

    def test_friends_hidden_when_logged_in_but_not_friends(self):
        print("\n[START] friends_hidden_when_logged_in_but_not_friends")
        self.client.login(username="user1", password="pass")
        url = reverse("entries:detail", kwargs={"author_serial": self.a2.serial, "entry_serial": self.friends_entry.serial})
        response = self.client.get(url)
        if response.status_code == 200:
            self.assertNotContains(response, "friends post")
        else:
            self.assertEqual(response.status_code, 403)
        print("[END] friends_hidden_when_logged_in_but_not_friends Passed")

    def test_friends_visible_to_mutual_followers(self):
        print("\n[START] friends_visible_to_mutual_followers")
        FollowRequest.objects.create(actor=self.a1, author_followed=self.a2, state=FollowRequest.State.ACCEPTED)
        FollowRequest.objects.create(actor=self.a2, author_followed=self.a1, state=FollowRequest.State.ACCEPTED)
        self.client.login(username="user1", password="pass")
        url = reverse("entries:detail", kwargs={"author_serial": self.a2.serial, "entry_serial": self.friends_entry.serial})
        response = self.client.get(url)
        self.assertContains(response, "friends post")
        print("[END] friends_visible_to_mutual_followers Passed")

    def test_author_can_see_own_friends_post(self):
        print("\n[START] author_can_see_own_friends_post")
        self.client.login(username="user2", password="pass")
        url = reverse("entries:detail", kwargs={"author_serial": self.a2.serial, "entry_serial": self.friends_entry.serial})
        response = self.client.get(url)
        self.assertContains(response, "friends post")
        print("[END] author_can_see_own_friends_post Passed")

    def test_deleted_entry_returns_403(self):
        print("\n[START] deleted_entry_returns_403")
        url = reverse("entries:detail", kwargs={"author_serial": self.a2.serial, "entry_serial": self.deleted_entry.serial})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        print("[END] deleted_entry_returns_403 Passed")

    def test_unlisted_visible_when_logged_in_as_other_user(self):
        print("\n[START] unlisted_visible_when_logged_in_as_other_user")
        self.client.login(username="user1", password="pass")
        url = reverse("entries:detail", kwargs={"author_serial": self.a2.serial, "entry_serial": self.unlisted_entry.serial})
        response = self.client.get(url)
        self.assertContains(response, "unlisted post")
        print("[END] unlisted_visible_when_logged_in_as_other_user Passed")

    def test_friends_not_visible_with_one_way_follow(self):
        print("\n[START] friends_not_visible_with_one_way_follow")
        FollowRequest.objects.create(actor=self.a1, author_followed=self.a2, state=FollowRequest.State.ACCEPTED)
        self.client.login(username="user1", password="pass")
        url = reverse("entries:detail", kwargs={"author_serial": self.a2.serial, "entry_serial": self.friends_entry.serial})
        response = self.client.get(url)
        if response.status_code == 200:
            self.assertNotContains(response, "friends post")
        else:
            self.assertEqual(response.status_code, 403)
        print("[END] friends_not_visible_with_one_way_follow Passed")

    def test_public_entry_still_403_when_marked_deleted(self):
        print("\n[START] public_entry_still_403_when_marked_deleted")
        self.public_entry.visibility = Entry.Visibility.DELETED
        self.public_entry.save()
        url = reverse("entries:detail", kwargs={"author_serial": self.a2.serial, "entry_serial": self.public_entry.serial})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        print("[END] public_entry_still_403_when_marked_deleted Passed")