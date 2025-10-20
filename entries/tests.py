from django.test import TestCase, Client
from authors.models import Author
from .models import Entry, Comment, Like, EntryDelivery
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse


class CommentsLikesTests(TestCase):
	def setUp(self):
		# create two local authors
		self.a1 = Author.objects.create(id='http://local/api/authors/1', serial='1', displayName='A1')
		self.a2 = Author.objects.create(id='http://local/api/authors/2', serial='2', displayName='A2')
		# public entry by a2
		self.entry_public = Entry.objects.create(fqid='http://local/api/authors/2/entries/10', serial='10', author=self.a2, content='hello', visibility=Entry.Visibility.PUBLIC, published=timezone.now())
		# friends-only entry by a2
		self.entry_friends = Entry.objects.create(fqid='http://local/api/authors/2/entries/11', serial='11', author=self.a2, content='friends only', visibility=Entry.Visibility.FRIENDS, published=timezone.now())
		# unlisted entry by a2 (deliver to a1)
		self.entry_unlisted = Entry.objects.create(fqid='http://local/api/authors/2/entries/12', serial='12', author=self.a2, content='unlisted', visibility=Entry.Visibility.UNLISTED, published=timezone.now())
		EntryDelivery.objects.create(entry=self.entry_unlisted, recipient_author_fqid=self.a1.id)

		self.client = Client()

	def test_comment_public(self):
		# a1 comments on a2's public entry
		payload = {'comment': 'nice', 'id': 'http://remote/comment/1'}
		resp = self.client.post(f'/api/authors/2/entries/10/comments/', data=payload, content_type='application/json', **{'HTTP_X_AUTHOR_ID': self.a1.id})
		self.assertEqual(resp.status_code, 201)
		self.assertEqual(Comment.objects.filter(entry=self.entry_public).count(), 1)

	def test_like_public(self):
		# a1 likes public entry
		payload = {}
		resp = self.client.post(f'/api/authors/2/entries/10/likes/', data=payload, content_type='application/json', **{'HTTP_X_AUTHOR_ID': self.a1.id})
		self.assertEqual(resp.status_code, 201)
		self.assertEqual(Like.objects.filter(object_fqid=self.entry_public.fqid).count(), 1)

	def test_like_duplicate_idempotent(self):
		resp1 = self.client.post(f'/api/authors/2/entries/10/likes/', data={}, content_type='application/json', **{'HTTP_X_AUTHOR_ID': self.a1.id})
		self.assertEqual(resp1.status_code, 201)
		resp2 = self.client.post(f'/api/authors/2/entries/10/likes/', data={}, content_type='application/json', **{'HTTP_X_AUTHOR_ID': self.a1.id})
		self.assertIn(resp2.status_code, (200, 201))
		self.assertEqual(Like.objects.filter(author=self.a1, object_fqid=self.entry_public.fqid).count(), 1)

	def test_comment_friends_visibility(self):
		# Without friendship, a1 cannot comment on friends-only
		resp = self.client.post(f'/api/authors/2/entries/11/comments/', data={'comment': 'hi'}, content_type='application/json', **{'HTTP_X_AUTHOR_ID': self.a1.id})
		self.assertEqual(resp.status_code, 403)

	def test_comment_unlisted_only_recipient(self):
		# a1 is a delivered recipient and can comment
		resp = self.client.post(f'/api/authors/2/entries/12/comments/', data={'comment': 'secret'}, content_type='application/json', **{'HTTP_X_AUTHOR_ID': self.a1.id})
		self.assertEqual(resp.status_code, 201)

class EntryViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.client = Client()
        self.client.login(username="testuser", password="password")

        self.author = Author.objects.create(
            user=self.user,
            displayName="Test Author",
            host="http://localhost"
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
        url = reverse(
            "entries:entry_delete",
            kwargs={"author_serial": self.author.serial, "entry_serial": self.entry.serial}
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Entry.objects.filter(serial=self.entry.serial).exists())