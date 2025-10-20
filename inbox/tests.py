from django.test import TestCase, Client
from django.contrib.auth.models import User
from authors.models import Author
from .models import FollowRequest
import json

class FollowersAndFollowRequestsTests(TestCase):
    def setUp(self):
        # Create two users and link them to local authors
        self.user1 = User.objects.create_user(username="a1", password="pass1234")
        self.user2 = User.objects.create_user(username="a2", password="pass1234")

        self.a1 = Author.objects.create(
            id="http://local/api/authors/1",
            serial="1",
            user=self.user1,
            host="http://local/api/",
            displayName="A1",
        )
        self.a2 = Author.objects.create(
            id="http://local/api/authors/2",
            serial="2",
            user=self.user2,
            host="http://local/api/",
            displayName="A2",
        )

    def test_create_friend_request_object(self):
        """Tests creating friend request object"""

        # A1 requests to follow A2
        payload = {
            "type": "follow",
            "summary": f"{self.a1.displayName} wants to follow {self.a2.displayName}",
            "actor": {
                "type": "author",
                "id": self.a1.id,
                "host": self.a1.host,
                "displayName": self.a1.displayName,
                "github": self.a1.github,
                "profileImage": self.a1.profileImage,
                "web": self.a1.web,
            },
            "object": {
                "type": "author",
                "id": self.a2.id,
                "host": self.a2.host,
                "displayName": self.a2.displayName,
                "github": self.a2.github,
                "profileImage": self.a2.profileImage,
                "web": self.a2.web,
            },
        }

        response = self.client.post(
            f"/api/authors/{self.a2.serial}/inbox/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        # Assert staus code is 201
        self.assertEqual(response.status_code, 201)

        resp_json = response.json()
        # Assert status is 'created'
        self.assertEqual(resp_json.get("status"), "created")

        # assert that the request exists with the state requesting
        fr_exists = FollowRequest.objects.filter(
            actor=self.a1,
            author_followed=self.a2,
            state=FollowRequest.State.REQUESTING,
        ).exists()
        self.assertTrue(fr_exists)

    def test_create_friend_request_already_exists(self):
        """Tests retrieving friend request object instead of creating a new one"""
        # A1 requests to follow A2
        payload = {
            "type": "follow",
            "summary": f"{self.a1.displayName} wants to follow {self.a2.displayName}",
            "actor": {
                "type": "author",
                "id": self.a1.id,
                "host": self.a1.host,
                "displayName": self.a1.displayName,
                "github": self.a1.github,
                "profileImage": self.a1.profileImage,
                "web": self.a1.web,
            },
            "object": {
                "type": "author",
                "id": self.a2.id,
                "host": self.a2.host,
                "displayName": self.a2.displayName,
                "github": self.a2.github,
                "profileImage": self.a2.profileImage,
                "web": self.a2.web,
            },
        }

        response = self.client.post(
            f"/api/authors/{self.a2.serial}/inbox/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        resp_json = response.json()
        # Assert status is 'created'
        self.assertEqual(resp_json.get("status"), "created")

        response = self.client.post(
            f"/api/authors/{self.a2.serial}/inbox/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)

        resp_json = response.json()
        # Assert status is 'exists'
        self.assertEqual(resp_json.get("status"), "exists")

        # assert that the request exists with the state requesting
        fr_exists = FollowRequest.objects.filter(
            actor=self.a1,
            author_followed=self.a2,
            state=FollowRequest.State.REQUESTING,
        ).exists()
        self.assertTrue(fr_exists)

    def test_create_friend_request_missing_object(self):
        """Tests creating a new friend request with no object"""
        # A1 requests to follow "no author"
        payload = {
            "type": "follow",
            "summary": f"{self.a1.displayName} wants to follow {self.a2.displayName}",
            "actor": {
                "type": "author",
                "id": self.a1.id,
                "host": self.a1.host,
                "displayName": self.a1.displayName,
                "github": self.a1.github,
                "profileImage": self.a1.profileImage,
                "web": self.a1.web,
            },
        }

        response = self.client.post(
            f"/api/authors/{self.a2.serial}/inbox/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        resp_json = response.json()
        # Assert detail is 'error'
        self.assertEqual(resp_json.get("detail"), "error")

        # Assert status code is 400
        self.assertEqual(response.status_code, 400)

        # assert that the request doesn't exist
        fr_exists = FollowRequest.objects.filter(
            actor=self.a1,
            author_followed=self.a2,
            state=FollowRequest.State.REQUESTING,
        ).exists()
        self.assertFalse(fr_exists)