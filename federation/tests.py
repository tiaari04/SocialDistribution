"""
Tests for the simplified federation system (None and Basic Auth only).
"""
from unittest.mock import patch, Mock
from django.test import TestCase
from django.utils import timezone
from authors.models import Author
from federation.models import FederatedNode, FederationLog
from federation.utils import send_entry_to_federation, get_federation_status, _build_entry_payload


class FederatedNodeModelTests(TestCase):
    """Test FederatedNode model functionality"""
    
    def setUp(self):
        self.node = FederatedNode.objects.create(
            name="Test Node",
            base_url="https://test-node.com",
            auth_method=FederatedNode.AuthMethod.BASIC,
            username="testuser",
            password="testpass",
            is_active=True
        )
    
    def test_node_creation(self):
        """Test creating a federated node"""
        self.assertEqual(self.node.name, "Test Node")
        self.assertEqual(self.node.base_url, "https://test-node.com")
        self.assertTrue(self.node.is_active)
    
    def test_full_inbox_url(self):
        """Test inbox URL construction"""
        expected_url = "https://test-node.com/api/authors/"
        self.assertEqual(self.node.full_inbox_url, expected_url)
    
    def test_success_rate_calculation(self):
        """Test success rate calculation"""
        self.assertEqual(self.node.success_rate, 0.0)
        
        self.node.total_sends = 10
        self.node.total_failures = 2
        self.assertEqual(self.node.success_rate, 80.0)
        
        self.node.total_sends = 100
        self.node.total_failures = 0
        self.assertEqual(self.node.success_rate, 100.0)
    
    def test_record_success(self):
        """Test recording a successful send"""
        initial_sends = self.node.total_sends
        self.node.record_success()
        self.node.refresh_from_db()
        
        self.assertEqual(self.node.total_sends, initial_sends + 1)
        self.assertEqual(self.node.total_failures, 0)
        self.assertIsNotNone(self.node.last_successful_send)
    
    def test_record_failure(self):
        """Test recording a failed send"""
        initial_sends = self.node.total_sends
        initial_failures = self.node.total_failures
        self.node.record_failure()
        self.node.refresh_from_db()
        
        self.assertEqual(self.node.total_sends, initial_sends + 1)
        self.assertEqual(self.node.total_failures, initial_failures + 1)
        self.assertIsNotNone(self.node.last_failed_send)
    
    def test_get_auth_headers_none(self):
        """Test auth headers with no authentication"""
        node = FederatedNode.objects.create(
            name="No Auth Node",
            base_url="https://no-auth.com",
            auth_method=FederatedNode.AuthMethod.NONE
        )
        headers = node.get_auth_headers()
        self.assertEqual(headers['Content-Type'], 'application/json')
        self.assertNotIn('Authorization', headers)
    
    def test_get_auth_headers_basic(self):
        """Test auth headers with basic authentication"""
        headers = self.node.get_auth_headers()
        self.assertIn('Authorization', headers)
        self.assertTrue(headers['Authorization'].startswith('Basic '))


class FederationUtilsTests(TestCase):
    """Test federation utility functions"""
    
    def setUp(self):
        # Create test author
        self.author = Author.objects.create(
            id="http://localhost:8000/api/authors/test123",
            host="http://localhost:8000/api/",
            displayName="Test Author",
            serial="test123",
            is_local=True
        )
        
        # Create test nodes
        self.active_node = FederatedNode.objects.create(
            name="Active Node",
            base_url="https://active-node.com",
            is_active=True,
            auth_method=FederatedNode.AuthMethod.NONE
        )
        
        self.inactive_node = FederatedNode.objects.create(
            name="Inactive Node",
            base_url="https://inactive-node.com",
            is_active=False
        )
    
    def test_build_entry_payload(self):
        """Test building entry payload"""
        entry_dict = {
            "fqid": "http://localhost:8000/api/entries/entry123",
            "author_id": "http://localhost:8000/api/authors/test123",
            "title": "Test Entry",
            "content": "Test content",
            "visibility": "public",
            "created": timezone.now(),
            "published": timezone.now(),
            "updated": timezone.now(),
        }
        
        payload = _build_entry_payload(entry_dict)
        
        self.assertEqual(payload['title'], 'Test Entry')
        self.assertEqual(payload['content'], 'Test content')
        self.assertIn('author_data', payload)
        self.assertEqual(payload['author_data']['displayName'], 'Test Author')
    
    @patch('federation.utils.requests.post')
    def test_send_to_active_nodes_only(self, mock_post):
        """Test that entries are only sent to active nodes"""
        mock_post.return_value = Mock(status_code=200, text='OK')
        
        entry_dict = {
            "fqid": "http://localhost:8000/api/entries/entry123",
            "author_id": "http://localhost:8000/api/authors/test123",
            "title": "Test Entry",
            "content": "Test content",
            "created": timezone.now(),
            "published": timezone.now(),
            "updated": timezone.now(),
        }
        
        results = send_entry_to_federation(entry_dict)
        
        # Should only send to active node
        self.assertEqual(results['successful'], 1)
        self.assertEqual(results['failed'], 0)
        self.assertEqual(mock_post.call_count, 1)
    
    @patch('federation.utils.requests.post')
    def test_send_entry_success(self, mock_post):
        """Test successful entry sending"""
        mock_post.return_value = Mock(status_code=200, text='{"status": "ok"}')
        
        entry_dict = {
            "fqid": "http://localhost:8000/api/entries/entry123",
            "author_id": "http://localhost:8000/api/authors/test123",
            "title": "Test Entry",
            "content": "Test content",
            "created": timezone.now(),
            "published": timezone.now(),
            "updated": timezone.now(),
        }
        
        results = send_entry_to_federation(entry_dict)
        
        self.assertEqual(results['successful'], 1)
        self.assertEqual(results['failed'], 0)
        
        # Check log was created
        log = FederationLog.objects.first()
        self.assertIsNotNone(log)
        self.assertEqual(log.status, FederationLog.Status.SUCCESS)
        self.assertEqual(log.response_status_code, 200)
        
        # Check node statistics updated
        self.active_node.refresh_from_db()
        self.assertEqual(self.active_node.total_sends, 1)
        self.assertEqual(self.active_node.total_failures, 0)
    
    @patch('federation.utils.requests.post')
    def test_send_entry_failure(self, mock_post):
        """Test failed entry sending"""
        mock_post.return_value = Mock(status_code=500, text='Internal Server Error')
        
        entry_dict = {
            "fqid": "http://localhost:8000/api/entries/entry123",
            "author_id": "http://localhost:8000/api/authors/test123",
            "title": "Test Entry",
            "content": "Test content",
            "created": timezone.now(),
            "published": timezone.now(),
            "updated": timezone.now(),
        }
        
        results = send_entry_to_federation(entry_dict)
        
        self.assertEqual(results['successful'], 0)
        self.assertEqual(results['failed'], 1)
        
        # Check log was created
        log = FederationLog.objects.first()
        self.assertIsNotNone(log)
        self.assertEqual(log.status, FederationLog.Status.FAILURE)
        self.assertEqual(log.response_status_code, 500)
        
        # Check node statistics updated
        self.active_node.refresh_from_db()
        self.assertEqual(self.active_node.total_sends, 1)
        self.assertEqual(self.active_node.total_failures, 1)
    
    @patch('federation.utils.requests.post')
    def test_send_entry_network_error(self, mock_post):
        """Test network error handling"""
        mock_post.side_effect = Exception("Network unreachable")
        
        entry_dict = {
            "fqid": "http://localhost:8000/api/entries/entry123",
            "author_id": "http://localhost:8000/api/authors/test123",
            "title": "Test Entry",
            "content": "Test content",
            "created": timezone.now(),
            "published": timezone.now(),
            "updated": timezone.now(),
        }
        
        results = send_entry_to_federation(entry_dict)
        
        self.assertEqual(results['successful'], 0)
        self.assertEqual(results['failed'], 1)
        
        # Check error was logged
        log = FederationLog.objects.first()
        self.assertEqual(log.status, FederationLog.Status.FAILURE)
        self.assertIn('Network unreachable', log.error_message)
    
    def test_get_federation_status(self):
        """Test getting federation status"""
        status = get_federation_status()
        
        self.assertEqual(status['total_nodes'], 2)
        self.assertEqual(status['active_nodes'], 1)
        self.assertEqual(len(status['nodes']), 2)


class MultinodeFederationTests(TestCase):
    """Test federation with multiple nodes (None and Basic Auth only)"""
    
    def setUp(self):
        self.author = Author.objects.create(
            id="http://localhost:8000/api/authors/test123",
            host="http://localhost:8000/api/",
            displayName="Test Author",
            serial="test123"
        )
        
        # Create nodes with None and Basic auth only
        self.nodes = [
            FederatedNode.objects.create(
                name="Node 1 - No Auth",
                base_url="https://node1.com",
                auth_method=FederatedNode.AuthMethod.NONE,
                is_active=True
            ),
            FederatedNode.objects.create(
                name="Node 2 - Basic Auth",
                base_url="https://node2.com",
                auth_method=FederatedNode.AuthMethod.BASIC,
                username="user2",
                password="pass2",
                is_active=True
            ),
            FederatedNode.objects.create(
                name="Node 3 - Inactive",
                base_url="https://node3.com",
                is_active=False
            ),
        ]
    
    @patch('federation.utils.requests.post')
    def test_send_to_multiple_nodes(self, mock_post):
        """Test sending entry to multiple nodes with different auth"""
        # Simulate responses from nodes
        responses = [
            Mock(status_code=200, text='OK'),  # Node 1 - No auth
            Mock(status_code=201, text='Created'),  # Node 2 - Basic auth
        ]
        mock_post.side_effect = responses
        
        entry_dict = {
            "fqid": "http://localhost:8000/api/entries/entry123",
            "author_id": "http://localhost:8000/api/authors/test123",
            "title": "Multi-node Test",
            "content": "Testing multiple nodes",
            "created": timezone.now(),
            "published": timezone.now(),
            "updated": timezone.now(),
        }
        
        results = send_entry_to_federation(entry_dict)
        
        # Should send to 2 active nodes (not the inactive one)
        self.assertEqual(mock_post.call_count, 2)
        self.assertEqual(results['successful'], 2)
        self.assertEqual(results['failed'], 0)
        
        # Verify correct auth headers were used
        calls = mock_post.call_args_list
        
        # Node 1 - No auth
        self.assertNotIn('Authorization', calls[0][1]['headers'])
        
        # Node 2 - Basic auth
        self.assertIn('Authorization', calls[1][1]['headers'])
        self.assertTrue(calls[1][1]['headers']['Authorization'].startswith('Basic '))
        
        # Check logs were created for all attempts
        logs = FederationLog.objects.all()
        self.assertEqual(logs.count(), 2)
        
        # Check node statistics
        for node in self.nodes[:2]:  # First 2 are active
            node.refresh_from_db()
            self.assertEqual(node.total_sends, 1)
            self.assertEqual(node.total_failures, 0)
