from django.db import models
from django.core.validators import URLValidator
from django.utils import timezone


class FederatedNode(models.Model):
    """
    Represents a federated node (friend server) that we exchange data with.
    """
    class AuthMethod(models.TextChoices):
        NONE = 'none', 'None'
        BASIC = 'basic', 'Basic Auth'
    
    # Basic Information
    name = models.CharField(max_length=255, unique=True, help_text="Friendly name for this node")
    base_url = models.URLField(max_length=500, validators=[URLValidator()], help_text="Base URL of the node (e.g., https://example.com)")
    api_version = models.CharField(max_length=20, default="v1", help_text="API version this node uses")
    
    # Authentication
    auth_method = models.CharField(
        max_length=20,
        choices=AuthMethod.choices,
        default=AuthMethod.NONE,
        help_text="Authentication method to use"
    )
    username = models.CharField(max_length=255, blank=True, help_text="Username for Basic Auth")
    password = models.CharField(max_length=255, blank=True, help_text="Password for Basic Auth")
    token = models.CharField(max_length=500, blank=True, help_text="Bearer token or API key")
    
    # Status and Configuration
    is_active = models.BooleanField(default=True, help_text="Enable/disable this node")
    is_bidirectional = models.BooleanField(default=True, help_text="Can this node send data to us?")
    
    # Identifying my node
    is_local = models.BooleanField(default=False, help_text="Checks if this node is for this server")

    # Endpoints (allow customization per node)
    inbox_endpoint = models.CharField(max_length=200, default="/api/authors/", help_text="Endpoint for sending entries")
    
    # Metadata
    description = models.TextField(blank=True, help_text="Notes about this node")
    admin_contact = models.EmailField(blank=True, help_text="Admin contact for this node")
    
    # Statistics
    last_successful_send = models.DateTimeField(null=True, blank=True)
    last_failed_send = models.DateTimeField(null=True, blank=True)
    total_sends = models.IntegerField(default=0)
    total_failures = models.IntegerField(default=0)
    
    # Timestamps
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Federated Node"
        verbose_name_plural = "Federated Nodes"
    
    def __str__(self):
        status = "✓" if self.is_active else "✗"
        return f"{status} {self.name} ({self.base_url})"
    
    @property
    def full_inbox_url(self):
        """Construct the complete inbox URL"""
        base = self.base_url.rstrip('/')
        endpoint = self.inbox_endpoint.lstrip('/')
        return f"{base}/{endpoint}"
    
    @property
    def success_rate(self):
        """Calculate success rate percentage"""
        if self.total_sends == 0:
            return 0.0
        return ((self.total_sends - self.total_failures) / self.total_sends) * 100
    
    def record_success(self):
        """Record a successful send"""
        self.last_successful_send = timezone.now()
        self.total_sends += 1
        self.save(update_fields=['last_successful_send', 'total_sends'])
    
    def record_failure(self):
        """Record a failed send"""
        self.last_failed_send = timezone.now()
        self.total_sends += 1
        self.total_failures += 1
        self.save(update_fields=['last_failed_send', 'total_sends', 'total_failures'])
    
    def get_auth_headers(self):
        """Generate authentication headers based on auth method"""
        headers = {'Content-Type': 'application/json'}
        
        if self.auth_method == self.AuthMethod.BASIC and self.username:
            import base64
            credentials = f"{self.username}:{self.password}"
            encoded = base64.b64encode(credentials.encode()).decode()
            headers['Authorization'] = f"Basic {encoded}"
            print(self.username)
        
        return headers


class FederationLog(models.Model):
    """
    Log of federation activities for debugging and monitoring.
    """
    class Status(models.TextChoices):
        SUCCESS = 'success', 'Success'
        FAILURE = 'failure', 'Failure'
        PENDING = 'pending', 'Pending'
    
    node = models.ForeignKey(FederatedNode, on_delete=models.CASCADE, related_name='logs')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # Request details
    entry_fqid = models.CharField(max_length=500, help_text="FQID of the entry being sent")
    request_payload = models.JSONField(blank=True, null=True, help_text="Request payload sent")
    
    # Response details
    response_status_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True, help_text="Response from the node")
    error_message = models.TextField(blank=True, help_text="Error message if failed")
    
    # Timing
    created = models.DateTimeField(auto_now_add=True)
    completed = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created']
        verbose_name = "Federation Log"
        verbose_name_plural = "Federation Logs"
        indexes = [
            models.Index(fields=['-created']),
            models.Index(fields=['node', '-created']),
        ]
    
    def __str__(self):
        return f"{self.status} - {self.node.name} - {self.entry_fqid[:50]}"
