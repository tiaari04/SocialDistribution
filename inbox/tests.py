from django.test import TestCase, Client
from django.contrib.auth.models import User
from authors.models import Author
from .models import FollowRequest
from .services import get_follower, add_follower, remove_follower
import json
from unittest.mock import patch

class FollowersAndFollowRequestsTests(TestCase):
    def setUp(self):
        # Create two users and link them to local authors
        self.user1 = User.objects.create_user(username="a1", password="pass1234")
        self.user2 = User.objects.create_user(username="a2", password="pass1234")
        self.user3 = User.objects.create_user(username="a3", password="pass1234")
        self.user4 = User.objects.create_user(username="a4", password="pass1234")

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
        self.a3 = Author.objects.create(
            id="http://local/api/authors/3",
            serial="3",
            user=self.user3,
            host="http://local/api/",
            displayName="A3",
        )

        self.a4 = Author.objects.create(
            id="http://remote/api/authors/4",
            serial="4",
            user=self.user4,
            host="http://remote/api/",
            displayName="A4",
        )

# Tests for inbox API
    def test_create_follow_request_object(self):
        """Tests creating friend request object"""
        print("Inbox Tests: Tests creating friend request object")

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

    def test_create_follow_request_already_exists(self):
        """Tests retrieving friend request object instead of creating a new one"""
        print("Inbox Tests: Tests retrieving friend request object instead of creating a new one")
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

    def test_create_follow_request_missing_object(self):
        """Tests creating a new friend request with no object"""
        print("Inbox Tests: Tests creating a new friend request with no object")
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

# Tests for followers API
    def test_approve_follow_request(self):
        """Approving follow request logged in as correct author"""
        print("Inbox Tests: Tests approving follow request logged in as correct author")
        # Login as a1 (the follower)
        self.client = Client()
        self.client.force_login(self.user2)

        # A1 sends request to A2
        follow_request = FollowRequest.objects.create(
            actor=self.a1,
            author_followed=self.a2,
            state=FollowRequest.State.REQUESTING
        )

        # PUT request to accept follow request
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
        """Rejecting follow request logged in as correct author"""
        print("Inbox Tests: Tests rejecting follow request logged in as correct author")
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
        response = self.client.delete(
            f"/api/authors/{self.a2.serial}/followers/{self.a1.id}/",
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"detail": "Follower removed"})

        # Check that the FollowRequest was deleted from the database
        self.assertFalse(FollowRequest.objects.filter(actor=self.a1, author_followed=self.a2).exists())

    def test_reject_follow_request_wrong_author(self):
        """Rejecting follow request logged in as incorrect author"""
        print("Inbox Tests: Tests rejecting follow request logged in as incorrect author")
        # Login as a3 
        self.client = Client()
        self.client.force_login(self.user3)

        # A1 sends request to A2
        follow_request = FollowRequest.objects.create(
            actor=self.a1,
            author_followed=self.a2,
            state=FollowRequest.State.REQUESTING
        )

        # PUT request to reject follow request
        response = self.client.delete(
            f"/api/authors/{self.a2.serial}/followers/{self.a1.id}/",
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "Authentication required"})

        # Check that the FollowRequest state has not changed
        follow_request.refresh_from_db()
        self.assertEqual(follow_request.state, FollowRequest.State.REQUESTING)

    def test_approve_follow_request_fake_author(self):
        """Approving follow request logged in as fake author"""
        print("Inbox Tests: Tests approving follow request logged in as fake author")
        # A1 sends request to A2
        follow_request = FollowRequest.objects.create(
            actor=self.a1,
            author_followed=self.a2,
            state=FollowRequest.State.REQUESTING
        )
        
        # fake author serial
        fake_serial = "5"

        # DELETE request to reject follow request
        response = self.client.put(
            f"/api/authors/{fake_serial}/followers/{self.a1.id}/",
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 404)

        # Check that the FollowRequest state has not changed
        follow_request.refresh_from_db()
        self.assertEqual(follow_request.state, FollowRequest.State.REQUESTING)

    def test_get_follower_exists(self):
        """Tests GET for an author's follower and that follower exists"""
        print("Inbox Tests: Tests GET for an author's follower and that follower exists")
        # Login as a2 (the follower)
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
        """Tests GET for an author's follower and that follower does not exist"""
        print("Inbox Tests: Tests GET for an author's follower and that follower does not exist")
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

    def test_approve_follow_request_incorrect_author(self):
        """Approving follow request logged in as incorrect author"""
        print("Inbox Tests: Tests approving follow request logged in as incorrect author (fails)")
        # Login as a1 (the follower)
        self.client = Client()
        self.client.force_login(self.user1)

        # A1 sends request to A2
        follow_request = FollowRequest.objects.create(
            actor=self.a1,
            author_followed=self.a2,
            state=FollowRequest.State.REQUESTING
        )
        
        # PUT request to accept follow request
        response = self.client.put(
            f"/api/authors/{self.a2.serial}/followers/{self.a1.id}/",
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 403)

        # Check that the FollowRequest state has not changed
        follow_request.refresh_from_db()
        self.assertEqual(follow_request.state, FollowRequest.State.REQUESTING)

    def test_POSTing_to_followers_API(self):
        """Test trying to post to followers api"""
        print("Inbox Tests: Tests trying to post to the followers API (returns 405)")
        response = self.client.post(
            f"/api/authors/{self.a2.serial}/followers/{self.a1.id}/",
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 405)

# Tests for followers API helper functions
    def test_get_follower_function_not_following(self):
        """Test result of get_follower helper function if a2 doesn't follow a1"""
        print("Inbox Tests: Tests result of get_follower helper function if a2 doesn't follow a1")
        result = get_follower(self.a1, self.a2)
        self.assertEqual(result, None)

    def test_get_follower_function_is_following(self):
        """Test result of get_follower helper function if a2 doesn't follow a1"""
        print("Inbox Tests: Tests result of get_follower helper function if a2 follows a1")

        follow_request = FollowRequest.objects.create(
            actor=self.a1,
            author_followed=self.a2,
            state=FollowRequest.State.ACCEPTED
        )

        result = get_follower(self.a2, self.a1)
        self.assertEqual(result, {"is_follower": True})

    def test_add_follower_accepting_request(self):
        """Test result of add_follower helper function if a2 sent a1 a follow request"""
        print("Inbox Tests: Tests result of add_follower helper function if a2 sent a1 a follow request")
        follow_request = FollowRequest.objects.create(
            actor=self.a1,
            author_followed=self.a2,
            state=FollowRequest.State.REQUESTING
        )

        result = add_follower(self.a2, self.a1)
        self.assertEqual(result.state, FollowRequest.State.ACCEPTED)

    def test_add_follower_already_following(self):
        """Test result of add_follower helper function if a2 already follows a1"""
        print("Inbox Tests: Tests result of add_follower helper function if a2 already follows a1")
        follow_request = FollowRequest.objects.create(
            actor=self.a1,
            author_followed=self.a2,
            state=FollowRequest.State.ACCEPTED
        )

        result = add_follower(self.a2, self.a1)
        self.assertEqual(result, follow_request)

    def test_add_follower_create_new(self):
        """Test result of add_follower helper function if there isn't a previous follow request"""
        print("Inbox Tests: Tests result of add_follower helper function if there isn't a previous follow request")
        follow_request = FollowRequest.objects.create(
            actor=self.a1,
            author_followed=self.a2,
            state=FollowRequest.State.ACCEPTED
        )

        result = add_follower(self.a2, self.a1)
        self.assertEqual(result, follow_request)

    def test_remove_follower_exists(self):
        """Test result of remove_follower helper function if there is a previous follow request"""
        print("Inbox Tests: Tests result of remove_follower helper function if there is a previous follow request")
        follow_request = FollowRequest.objects.create(
            actor=self.a1,
            author_followed=self.a2,
            state=FollowRequest.State.ACCEPTED
        )

        result = remove_follower(self.a2, self.a1)
        self.assertEqual(result.actor, follow_request.actor)
        self.assertEqual(result.author_followed, follow_request.author_followed)
        self.assertEqual(result.state, follow_request.state)

    def test_remove_follower_not_exists(self):
        """Test result of remove_follower helper function if there isn't a previous follow request"""
        print("Inbox Tests: Tests result of remove_follower helper function if there isn't a previous follow request")
  
        result = remove_follower(self.a2, self.a1)
        self.assertEqual(result, None)

    def test_followers_API_has_followers(self):
        """Test get /followers/ API if the author has followers"""
        print("Inbox Tests: Tests GET /followers/ API if the author has followers")
        follow_request1 = FollowRequest.objects.create(
            actor=self.a2,
            author_followed=self.a1,
            state=FollowRequest.State.ACCEPTED
        )
        follow_request2 = FollowRequest.objects.create(
            actor=self.a3,
            author_followed=self.a1,
            state=FollowRequest.State.ACCEPTED
        )

        # Login as a1
        self.client = Client()
        self.client.force_login(self.user1)

        response = self.client.get(
            f"/api/authors/{self.a1.serial}/followers/",
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["type"], "followers")

        follower_ids = [f["id"] for f in data["followers"]]
        expected_ids = [self.a2.id, self.a3.id]

        for expected_id in expected_ids:
            self.assertIn(expected_id, follower_ids)

    def test_followers_API_has_no_followers(self):
        """Test get /followers/ API if the author has no followers"""
        print("Inbox Tests: Tests GET /followers/ API if the author has no followers")

        # Login as a1
        self.client = Client()
        self.client.force_login(self.user1)

        response = self.client.get(
            f"/api/authors/{self.a1.serial}/followers/",
            content_type="application/json",
        )

        # Check the response
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["followers"], [])

# Tests for friends functionality
    def test_is_friend(self):
        """Tests if 2 authors have accepted requests they are friends"""
        print("Inbox Tests: Tests if 2 authors have accepted requests they are friends")
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
        """Test if 1 author has accepted request and the other hasn't they are not friends"""
        print("Inbox Tests: Tests if 1 author has accepted request and the other hasn't they are not friends")
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
        """Test if 1 author has accepted then removed request and the other hasn't they are not friends"""
        print("Inbox Tests: Tests if 1 author has accepted then removed request and the other hasn't they are not friends")
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

        self.client.force_login(self.user2)

        # Now one author unfollows the other
        response = self.client.delete(
            f"/api/authors/{self.a2.serial}/followers/{self.a1.id}/",
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"detail": "Follower removed"})

        # They are no longer friends
        self.assertFalse(self.a1.is_friend(self.a2))
        self.assertFalse(self.a2.is_friend(self.a1))

# Tests for following API
    def test_get_list_of_authors_following(self):
        """Test get /following/ API if the author is following anyone"""
        print("Inbox Tests: Tests GET /following/ API if the author is following anyone")
        follow_request1 = FollowRequest.objects.create(
            actor=self.a1,
            author_followed=self.a2,
            state=FollowRequest.State.ACCEPTED
        )
        follow_request2 = FollowRequest.objects.create(
            actor=self.a1,
            author_followed=self.a3,
            state=FollowRequest.State.ACCEPTED
        )

        # Login as a1
        self.client = Client()
        self.client.force_login(self.user1)

        response = self.client.get(
            f"/api/authors/{self.a1.serial}/following/",
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["type"], "following")

        following_ids = [f["id"] for f in data["followers"]]
        expected_ids = [self.a2.id, self.a3.id]

        for expected_id in expected_ids:
            self.assertIn(expected_id, following_ids)

    def test_get_list_of_authors_following_not_following_anyone(self):
        """Test get /following/ API if the author is following anyone"""
        print("Inbox Tests: Tests GET /following/ API if the author is following anyone")

        # Login as a1
        self.client = Client()
        self.client.force_login(self.user1)

        response = self.client.get(
            f"/api/authors/{self.a1.serial}/following/",
            content_type="application/json",
        )

        # Check the response
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["followers"], [])

    def test_get_list_of_authors_following_not_logged_in(self):
        """Test get /following/ API if the author is following anyone"""
        print("Inbox Tests: Tests GET /following/ API if the author is following anyone (not logged in)")
        follow_request1 = FollowRequest.objects.create(
            actor=self.a1,
            author_followed=self.a2,
            state=FollowRequest.State.ACCEPTED
        )
        follow_request2 = FollowRequest.objects.create(
            actor=self.a1,
            author_followed=self.a3,
            state=FollowRequest.State.ACCEPTED
        )

        response = self.client.get(
            f"/api/authors/{self.a1.serial}/following/",
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 403)

    def test_POSTing_to_following_API(self):
        """Test trying to post to following api"""
        print("Inbox Tests: Tests trying to post to the following API (returns 405)")
        response = self.client.post(
            f"/api/authors/{self.a2.serial}/following/{self.a1.id}/",
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 405)

    def test_get_author_followed_exists(self):
        """Tests GETting an author followed and that follower exists"""
        print("Inbox Tests: Tests GETting an author followed and that follower exists")
        # Login as a1 (the follower)
        self.client = Client()
        self.client.force_login(self.user1)

        # A1 sends request to A2
        follow_request = FollowRequest.objects.create(
            actor=self.a1,
            author_followed=self.a2,
            state=FollowRequest.State.ACCEPTED
        )

        # GET request to check if a1 is following a2
        response = self.client.get(
            f"/api/authors/{self.a1.serial}/following/{self.a2.id}/",
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.json(), {"is_following": True})

    def test_get_author_followed_not_exists(self):
        """Tests GETting an author followed and that follower doesn't exists"""
        print("Inbox Tests: Tests GETting an author followed and that follower doesn't exists")
        # Login as a1 (the follower)
        self.client = Client()
        self.client.force_login(self.user1)

        # GET request to check if a1 is following a2
        response = self.client.get(
            f"/api/authors/{self.a1.serial}/following/{self.a2.id}/",
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.json(), {"is_following": False})

    def test_PUT_to_following_API_local_req_exists(self):
        """Test PUT follow request to send follow request to local author, request already exists"""
        print("Inbox Tests: Test PUT follow request to local author, request already exists")
        follow_request1 = FollowRequest.objects.create(
            actor=self.a1,
            author_followed=self.a2,
            state=FollowRequest.State.ACCEPTED
        )

        # Login as a1 (the follower)
        self.client = Client()
        self.client.force_login(self.user1)

        # PUT request to send follow request
        response = self.client.put(
            f"/api/authors/{self.a1.serial}/following/{self.a2.id}/",
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"detail": "Follow request already exists"})

    def test_PUT_to_following_API_remote_req_exists(self):
        """Test PUT follow request to send follow request to remote author, request already exists"""
        print("Inbox Tests: Test PUT follow request to remote author, request already exists")
        follow_request1 = FollowRequest.objects.create(
            actor=self.a1,
            author_followed=self.a4,
            state=FollowRequest.State.ACCEPTED
        )

        # Login as a1 (the follower)
        self.client = Client()
        self.client.force_login(self.user1)

        # PUT request to send follow request
        response = self.client.put(
            f"/api/authors/{self.a1.serial}/following/{self.a4.id}/",
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"detail": "Follow request already exists"})

    def test_PUT_to_following_API_local_req_not_exists(self):
        """Test PUT follow request to send follow request to local author, request doesn't exist"""
        print("Inbox Tests: Test PUT follow request to local author, request doesn't exist")

        # Login as a1 (the follower)
        self.client = Client()
        self.client.force_login(self.user1)

        # PUT request to send follow request
        response = self.client.put(
            f"/api/authors/{self.a1.serial}/following/{self.a2.id}/",
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {"detail": "Follow request sent"})

    @patch("inbox.services.requests.post")
    def test_PUT_to_following_API_remote_req_not_exists(self, mock_post):
        """Test PUT follow request to send follow request to remote author, request doesn't exist"""
        print("Inbox Tests: Test PUT follow request to remote author, request doesn't exist")
        mock_post.return_value.status_code = 200

        # Login as a1 (the follower)
        self.client = Client()
        self.client.force_login(self.user1)

        # PUT request to send follow request
        response = self.client.put(
            f"/api/authors/{self.a1.serial}/following/{self.a4.id}/",
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {"detail": "Follow request sent"})

    def test_following_API_unfollow_author(self):
        """Test DELETE follow request to unfollow author"""
        print("Inbox Tests: Tests DELETE follow request to unfollow author")
        follow_request1 = FollowRequest.objects.create(
            actor=self.a2,
            author_followed=self.a1,
            state=FollowRequest.State.ACCEPTED
        )

        # Login as a1 (the follower)
        self.client = Client()
        self.client.force_login(self.user2)

        response = self.client.delete(
            f"/api/authors/{self.a2.serial}/following/{self.a1.id}/",
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"detail": "Author unfollowed"})
        
    def test_following_API_unfollow_author_not_logged_in(self):
        """Test DELETE follow request to unfollow author without logging in"""
        print("Inbox Tests: Tests DELETE follow request to unfollow author without logging in (fails)")
        follow_request1 = FollowRequest.objects.create(
            actor=self.a2,
            author_followed=self.a1,
            state=FollowRequest.State.ACCEPTED
        )

        response = self.client.delete(
            f"/api/authors/{self.a2.serial}/following/{self.a1.id}/",
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 403)

    def test_following_API_delete_pending_request(self):
        """Test DELETE follow request to remove pending follow request"""
        print("Inbox Tests: Tests DELETE follow request to remove pending follow request")
        follow_request1 = FollowRequest.objects.create(
            actor=self.a2,
            author_followed=self.a1,
            state=FollowRequest.State.REQUESTING
        )

        # Login as a1 (the follower)
        self.client = Client()
        self.client.force_login(self.user2)

        response = self.client.delete(
            f"/api/authors/{self.a2.serial}/following/{self.a1.id}/",
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"detail": "Author unfollowed"})

    def test_following_API_unfollow_req_not_exist(self):
        """Test DELETE follow request to unfollow author but never requested to follow"""
        print("Inbox Tests: Tests DELETE follow request to unfollow author but never requested to follow")
        # Login as a1 (the follower)
        self.client = Client()
        self.client.force_login(self.user1)

        response = self.client.delete(
            f"/api/authors/{self.a1.serial}/following/{self.a2.id}/",
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "You didn't follow this author"})

# Tests for follow request API
    def test_get_follow_requests_has_none(self):
        """Test get /follow_requests/ API if the author has requests, they don't"""
        print("Inbox Tests: Tests GET /follow_requests/ API if the author has requests, they don't")

        response = self.client.get(
            f"/api/authors/{self.a1.serial}/follow_requests/",
            content_type="application/json",
        )

        # Check the response
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["followers"], [])

    def test_get_follow_requests_has_some(self):
        """Test get /follow_requests/ API if the author has requests, they do"""
        print("Inbox Tests: Tests GET GET /follow_requests/ API if the author has requests, they do")
        follow_request1 = FollowRequest.objects.create(
            actor=self.a1,
            author_followed=self.a3,
            state=FollowRequest.State.REQUESTING
        )
        follow_request2 = FollowRequest.objects.create(
            actor=self.a2,
            author_followed=self.a3,
            state=FollowRequest.State.REQUESTING
        )

        response = self.client.get(
            f"/api/authors/{self.a3.serial}/follow_requests/",
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["type"], "follow requests")

        follow_reqs_ids = [f["id"] for f in data["followers"]]
        expected_ids = [self.a2.id, self.a1.id]

        for expected_id in expected_ids:
            self.assertIn(expected_id, follow_reqs_ids)
