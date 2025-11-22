from django.contrib import admin
from django.conf import settings
from django import forms
from .models import Author


class AuthorAdminForm(forms.ModelForm):
    """Custom form to handle URL field validation more gracefully"""
    
    class Meta:
        model = Author
        fields = '__all__'
        widgets = {
            'id': forms.TextInput(attrs={'size': 80}),
            'host': forms.TextInput(attrs={'size': 80}),
        }
    
    def clean_id(self):
        """Ensure id is a valid URL by prepending base if needed"""
        id_value = self.cleaned_data.get('id', '')
        if id_value and not id_value.startswith('http'):
            base = getattr(settings, 'NODE_API_BASE', 'http://localhost:8000/api/')
            if id_value.startswith('/'):
                id_value = base.rstrip('/') + id_value
            else:
                id_value = base.rstrip('/') + '/' + id_value
        return id_value
    
    def clean_host(self):
        """Ensure host is a valid URL"""
        host_value = self.cleaned_data.get('host', '')
        if host_value:
            if not host_value.startswith('http'):
                if host_value.startswith('/'):
                    # /api/ -> http://localhost:8000/api/
                    host_value = 'http://localhost:8000' + host_value
                else:
                    # localhost:8000 -> http://localhost:8000
                    host_value = 'http://' + host_value
        else:
            # Empty host, set default
            host_value = 'http://localhost:8000/api/'
        
        # Ensure it ends with a slash for consistency
        if not host_value.endswith('/'):
            host_value += '/'
        
        return host_value


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    form = AuthorAdminForm
    list_display = ("displayName", "is_local", "is_approved", "is_admin", "is_active", "serial")
    list_filter = ("is_local", "is_approved", "is_admin", "is_active")
    search_fields = ("displayName", "id", "host", "github", "web", "serial")
    list_editable = ("is_approved", "is_admin", "is_active")
    
    def get_fieldsets(self, request, obj=None):
        """Make id readonly when editing existing objects"""
        if obj:  # Editing existing object
            return (
                ('Identity', {
                    'fields': ('id', 'serial', 'user'),
                    'description': 'ID cannot be changed after creation (it is the primary key)'
                }),
                ('Profile', {
                    'fields': ('displayName', 'description', 'profileImage', 'github', 'web')
                }),
                ('Server Info', {
                    'fields': ('host', 'is_local'),
                }),
                ('Permissions', {
                    'fields': ('is_approved', 'is_admin', 'is_active'),
                    'description': 'Control user access and permissions'
                }),
                ('Timestamps', {
                    'fields': ('created', 'updated'),
                    'classes': ('collapse',)
                }),
            )
        else:  # Creating new object
            return (
                ('Identity', {
                    'fields': ('id', 'serial', 'user'),
                    'description': 'For Id field, you can enter just the path (e.g., /authors/ABC123) and it will be converted to a full URL'
                }),
                ('Profile', {
                    'fields': ('displayName', 'description', 'profileImage', 'github', 'web')
                }),
                ('Server Info', {
                    'fields': ('host', 'is_local'),
                    'description': 'Host will default to localhost if not a full URL'
                }),
                ('Permissions', {
                    'fields': ('is_approved', 'is_admin', 'is_active'),
                    'description': 'Control user access and permissions'
                }),
            )
    
    def get_readonly_fields(self, request, obj=None):
        """Make id and host readonly when editing (since they're URLs), along with timestamps"""
        if obj:  # Editing existing object
            return ('id', 'host', 'created', 'updated')
        return ('created', 'updated')
