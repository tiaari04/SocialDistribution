from django.test import TestCase, Client
from authors.models import Author
from .models import Entry, Comment, Like, EntryDelivery
from inbox.models import FollowRequest
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from inbox.models import FollowRequest

class CommentsLikesTests(TestCase):
    def setUp(self):
        # create two local authors
        self.a1 = Author.objects.create(id='http://local/api/authors/1', serial='1', displayName='A1')
        self.a2 = Author.objects.create(id='http://local/api/authors/2', serial='2', displayName='A2')
        # public entry by a2
        self.entry_public = Entry.objects.create(
            fqid='http://local/api/authors/2/entries/10',
            serial='10',
            author=self.a2,
            content='hello',
            visibility=Entry.Visibility.PUBLIC,
            published=timezone.now(),
        )
        # friends-only entry by a2
        self.entry_friends = Entry.objects.create(
            fqid='http://local/api/authors/2/entries/11',
            serial='11',
            author=self.a2,
            content='friends only',
            visibility=Entry.Visibility.FRIENDS,
            published=timezone.now(),
        )
        # unlisted entry by a2 (deliver to a1)
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
        # a1 comments on a2's public entry
        print("Entries test: comment_public — a1 posts a comment on a public entry")
        payload = {'comment': 'nice', 'id': 'http://remote/comment/1'}
        resp = self.client.post(
            f'/api/authors/2/entries/10/comments/',
            data=payload,
            content_type='application/json',
            **{'HTTP_X_AUTHOR_ID': self.a1.id},
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Comment.objects.filter(entry=self.entry_public).count(), 1)

    def test_like_public(self):
        # a1 likes public entry
        print("Entries test: like_public — a1 likes a public entry")
        payload = {}
        resp = self.client.post(
            f'/api/authors/2/entries/10/likes/',
            data=payload,
            content_type='application/json',
            **{'HTTP_X_AUTHOR_ID': self.a1.id},
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Like.objects.filter(object_fqid=self.entry_public.fqid).count(), 1)

    def test_like_duplicate_idempotent(self):
        print("Entries test: like_duplicate_idempotent — liking twice should be idempotent")
        resp1 = self.client.post(
            f'/api/authors/2/entries/10/likes/', data={}, content_type='application/json', **{'HTTP_X_AUTHOR_ID': self.a1.id}
        )
        self.assertEqual(resp1.status_code, 201)
        resp2 = self.client.post(
            f'/api/authors/2/entries/10/likes/', data={}, content_type='application/json', **{'HTTP_X_AUTHOR_ID': self.a1.id}
        )
        self.assertIn(resp2.status_code, (200, 201))
        self.assertEqual(Like.objects.filter(author=self.a1, object_fqid=self.entry_public.fqid).count(), 1)

    def test_comment_friends_visibility(self):
        # Without friendship, a1 cannot comment on friends-only
        print("Entries test: comment_friends_visibility — non-friends cannot comment on friends-only entries")
        resp = self.client.post(
            f'/api/authors/2/entries/11/comments/',
            data={'comment': 'hi'},
            content_type='application/json',
            **{'HTTP_X_AUTHOR_ID': self.a1.id},
        )
        self.assertEqual(resp.status_code, 403)

    def test_comment_unlisted_only_recipient(self):
        # a1 is a delivered recipient and can comment
        print("Entries test: comment_unlisted_only_recipient — unlisted recipient can comment")
        resp = self.client.post(
            f'/api/authors/2/entries/12/comments/',
            data={'comment': 'secret'},
            content_type='application/json',
            **{'HTTP_X_AUTHOR_ID': self.a1.id},
        )
        self.assertEqual(resp.status_code, 201)

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
            visibility="PUBLIC",
            published=timezone.now()
        )

    def test_create_entry(self):
        print("Entries test: create_entry — posting a new entry for author")
        url = reverse("entries:create", kwargs={"author_serial": self.author.serial})
        data = {
            "title": "New Post",
            "content": "New content",
            "content_type": "text/plain",
            "visibility": "PUBLIC"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Entry.objects.filter(title="New Post").exists())

    def test_edit_entry(self):
        print("Entries test: edit_entry — submitting edits to an entry")
        url = reverse(
            "entries:edit", 
            kwargs={"author_serial": self.author.serial, "entry_serial": self.entry.serial}
        )
        data = {
            "title": "Edited Post",
            "content": "Edited content",
            "content_type": "text/plain",
            "visibility": "PUBLIC"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        self.entry.refresh_from_db()
        self.assertEqual(self.entry.title, "Edited Post")
        self.assertEqual(self.entry.content, "Edited content")

    def test_delete_entry(self):
        print("Entries test: delete_entry — attempting to delete an entry")
        url = reverse(
            "entries:entry_delete",
            kwargs={"author_serial": self.author.serial, "entry_serial": self.entry.serial}
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        # The delete view performs a soft-delete (mark_deleted) — entry remains but visibility is DELETED.
        self.assertTrue(Entry.objects.filter(serial=self.entry.serial).exists())
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.visibility, Entry.Visibility.DELETED)
		
class EntryDetailVisibilityTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.user1 = User.objects.create_user(username="user1", password="pass")
        self.user2 = User.objects.create_user(username="user2", password="pass")
        self.a1 = Author.objects.create(id=f"http://testserver/api/authors/{self.user1.username}", user=self.user1, serial="a1", displayName="Author 1", host="http://localhost")
        self.a2 = Author.objects.create(id=f"http://testserver/api/authors/{self.user2.username}", user=self.user2, serial="a2", displayName="Author 2", host="http://localhost")

        self.public_entry = Entry.objects.create(
            author=self.a2,
            serial="public1",
            fqid=f"{self.a2.host}/authors/{self.a2.serial}/entries/public1",
            visibility=Entry.Visibility.PUBLIC,
            content="public post",
            published=timezone.now(),
        )
        self.unlisted_entry = Entry.objects.create(
            author=self.a2,
            serial="unlisted1",
            fqid=f"{self.a2.host}/authors/{self.a2.serial}/entries/unlisted1",
            visibility=Entry.Visibility.UNLISTED,
            content="unlisted post",
            published=timezone.now(),
        )
        self.friends_entry = Entry.objects.create(
            author=self.a2,
            serial="friends1",
            fqid=f"{self.a2.host}/authors/{self.a2.serial}/entries/friends1",
            visibility=Entry.Visibility.FRIENDS,
            content="friends post",
            published=timezone.now(),
        )

    def test_public_visible_to_anyone(self):
        print("Entries test: public_visible_to_anyone — anonymous can see public entry")
        url = reverse("entries:detail", kwargs={"author_serial": self.a2.serial, "entry_serial": self.public_entry.serial})
        response = self.client.get(url)
        self.assertContains(response, "public post")

    def test_unlisted_visible_even_when_logged_out(self):
        print("Entries test: unlisted_visible_even_when_logged_out — check visibility")
        url = reverse("entries:detail", kwargs={"author_serial": self.a2.serial, "entry_serial": self.unlisted_entry.serial})
        response = self.client.get(url)
        self.assertContains(response, "unlisted post")

    def test_friends_hidden_when_not_logged_in(self):
        print("Entries test: friends_hidden_when_not_logged_in — anonymous should not see friends-only")
        url = reverse("entries:detail", kwargs={"author_serial": self.a2.serial, "entry_serial": self.friends_entry.serial})
        response = self.client.get(url)
        self.assertNotContains(response, "friends post")

    def test_friends_hidden_when_logged_in_but_not_friends(self):
        print("Entries test: friends_hidden_when_logged_in_but_not_friends — logged-in non-friend check")
        self.client.login(username="user1", password="pass")
        url = reverse("entries:detail", kwargs={"author_serial": self.a2.serial, "entry_serial": self.friends_entry.serial})
        response = self.client.get(url)
        # The view may either return 403 Forbidden or 200 OK with the content omitted; accept both behaviors.
        if response.status_code == 200:
            self.assertNotContains(response, "friends post")
        else:
            self.assertEqual(response.status_code, 403)

    def test_friends_visible_to_mutual_followers(self):
        print("Entries test: friends_visible_to_mutual_followers — mutual follow check")

        FollowRequest.objects.create(actor=self.a1, author_followed=self.a2, state=FollowRequest.State.ACCEPTED)
        FollowRequest.objects.create(actor=self.a2, author_followed=self.a1, state=FollowRequest.State.ACCEPTED)

        self.client.login(username="user1", password="pass")
        url = reverse("entries:detail", kwargs={"author_serial": self.a2.serial, "entry_serial": self.friends_entry.serial})
        response = self.client.get(url)
        self.assertContains(response, "friends post")

    def test_author_can_see_own_friends_post(self):
        print("Entries test: author_can_see_own_friends_post — author viewing own friends-only post")
        self.client.login(username="user2", password="pass")
        url = reverse("entries:detail", kwargs={"author_serial": self.a2.serial, "entry_serial": self.friends_entry.serial})
        response = self.client.get(url)
        self.assertContains(response, "friends post")