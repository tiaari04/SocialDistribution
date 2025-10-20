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

    def test_approve_follow_request(self):
        """ Approving follow request logged in as correct author"""
        # Login as a1 (the follower)
        self.client = Client()
        self.client.force_login(self.user2)

        # A1 sends request to A2
        follow_request = FollowRequest.objects.create(
            actor=self.a1,
            author_followed=self.a2,
            state=FollowRequest.State.REQUESTING
        )

        # DELETE request to reject follow request
        response = self.client.put(
            f"/api/authors/{self.a2.serial}/followers/{self.a1.id}/",
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {"detail": "Follower added"})

        # Check that the FollowRequest state has been updated
        follow_request.refresh_from_db()
        self.assertEqual(follow_request.state, FollowRequest.State.ACCEPTED)

    def test_reject_follow_request(self):
        """ Rejecting follow request logged in as correct author"""
        # Login as a1 (the follower)
        self.client = Client()
        self.client.force_login(self.user2)

        # A1 sends request to A2
        follow_request = FollowRequest.objects.create(
            actor=self.a1,
            author_followed=self.a2,
            state=FollowRequest.State.REQUESTING
        )

        # PUT request to approve follow request
        response = self.client.delete(
            f"/api/authors/{self.a2.serial}/followers/{self.a1.id}/",
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"detail": "Follower removed"})

        # Check that the FollowRequest state has been updated
        follow_request.refresh_from_db()
        self.assertEqual(follow_request.state, FollowRequest.State.REJECTED)

    def test_reject_follow_request_wrong_author(self):
        """ Rejecting follow request logged in as incorrect author"""
        # Login as a1 (the follower)
        self.client = Client()
        self.client.force_login(self.user1)

        # A1 sends request to A2
        follow_request = FollowRequest.objects.create(
            actor=self.a1,
            author_followed=self.a2,
            state=FollowRequest.State.REQUESTING
        )

        # PUT request to approve follow request
        response = self.client.delete(
            f"/api/authors/{self.a2.serial}/followers/{self.a1.id}/",
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "Forbidden"})

        # Check that the FollowRequest state has been updated
        follow_request.refresh_from_db()
        self.assertEqual(follow_request.state, FollowRequest.State.REQUESTING)

    def test_approve_follow_request_fake_author(self):
        """ Approving follow request logged in as correct author"""
        # Login as a1 (the follower)
        self.client = Client()
        self.client.force_login(self.user2)

        # A1 sends request to A2
        follow_request = FollowRequest.objects.create(
            actor=self.a1,
            author_followed=self.a2,
            state=FollowRequest.State.REQUESTING
        )
        
        # fake author serial
        fake_serial = "3"

        # DELETE request to reject follow request
        response = self.client.put(
            f"/api/authors/{fake_serial}/followers/{self.a1.id}/",
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 404)

        # Check that the FollowRequest state has been updated
        follow_request.refresh_from_db()
        self.assertEqual(follow_request.state, FollowRequest.State.REQUESTING)

    def test_get_follower_exists(self):
        """ Approving follow request logged in as correct author"""
        # Login as a1 (the follower)
        self.client = Client()
        self.client.force_login(self.user2)

        # A1 sends request to A2
        follow_request = FollowRequest.objects.create(
            actor=self.a1,
            author_followed=self.a2,
            state=FollowRequest.State.ACCEPTED
        )

        # GET request to check if author is follower
        response = self.client.get(
            f"/api/authors/{self.a2.serial}/followers/{self.a1.id}/",
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.json(), {"is_follower": True})

    def test_get_follower_not_exists(self):
        """ Approving follow request logged in as correct author"""
        # Login as a1 (the follower)
        self.client = Client()
        self.client.force_login(self.user2)

        # GET request to check if author is follower
        response = self.client.get(
            f"/api/authors/{self.a2.serial}/followers/{self.a1.id}/",
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"is_follower": False})


    def test_is_friend(self):
        """Test if 2 authors have accepted requests they are friends"""
        # A1 accepts request from A2
        follow_request = FollowRequest.objects.create(
            actor=self.a1,
            author_followed=self.a2,
            state=FollowRequest.State.ACCEPTED
        )

        # A2 accepts request from A1
        follow_request2 = FollowRequest.objects.create(
            actor=self.a2,
            author_followed=self.a1,
            state=FollowRequest.State.ACCEPTED
        )

        # Check if they are friends
        self.assertTrue(self.a1.is_friend(self.a2))
        self.assertTrue(self.a2.is_friend(self.a1))

    def test_is_friend_not_friends(self):
        """Test if 1 authors have accepted request and the other hasn't they are not friends"""
        # A1 accepts request from A2
        follow_request = FollowRequest.objects.create(
            actor=self.a1,
            author_followed=self.a2,
            state=FollowRequest.State.ACCEPTED
        )

        # A2 accepts request from A1
        follow_request = FollowRequest.objects.create(
            actor=self.a2,
            author_followed=self.a1,
            state=FollowRequest.State.REQUESTING
        )

        # Check if they are friends
        self.assertFalse(self.a1.is_friend(self.a2))
        self.assertFalse(self.a2.is_friend(self.a1))

    def test_is_friend_not_friends_accepted_then_rejected(self):
        """Test if 1 authors have accepted request and the other hasn't they are not friends"""
        # A1 accepts request from A2
        follow_request = FollowRequest.objects.create(
            actor=self.a1,
            author_followed=self.a2,
            state=FollowRequest.State.ACCEPTED
        )

        # A2 accepts request from A1
        follow_request2 = FollowRequest.objects.create(
            actor=self.a2,
            author_followed=self.a1,
            state=FollowRequest.State.ACCEPTED
        )

        # Initially they are friends
        self.assertTrue(self.a1.is_friend(self.a2))
        self.assertTrue(self.a2.is_friend(self.a1))

        # Now one author rejects the request
        follow_request2.state = FollowRequest.State.REJECTED
        follow_request2.save()

        # They are no longer friends
        self.assertFalse(self.a1.is_friend(self.a2))
        self.assertFalse(self.a2.is_friend(self.a1))