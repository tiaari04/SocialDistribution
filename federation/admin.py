from django.contrib import admin
from django.utils.html import format_html
from .models import FederatedNode, FederationLog


@admin.register(FederatedNode)
class FederatedNodeAdmin(admin.ModelAdmin):
    list_display = [
        'status_indicator', 'name', 'base_url', 'auth_method', 
        'success_rate_display', 'last_successful_send', 'total_sends'
    ]
    list_filter = ['is_active', 'auth_method', 'is_bidirectional']
    search_fields = ['name', 'base_url', 'admin_contact']
    readonly_fields = [
        'created', 'updated', 'last_successful_send', 'last_failed_send',
        'total_sends', 'total_failures', 'success_rate_display', 'full_inbox_url'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'base_url', 'api_version', 'description', 'admin_contact')
        }),
        ('Authentication', {
            'fields': ('auth_method', 'username', 'password', 'token'),
            'description': 'Configure authentication for this node'
        }),
        ('Configuration', {
            'fields': ('is_active', 'is_bidirectional', 'inbox_endpoint', 'full_inbox_url')
        }),
        ('Statistics', {
            'fields': (
                'success_rate_display', 'total_sends', 'total_failures',
                'last_successful_send', 'last_failed_send'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    def status_indicator(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">● Active</span>')
        return format_html('<span style="color: red;">● Inactive</span>')
    status_indicator.short_description = 'Status'
    
    def success_rate_display(self, obj):
        rate = obj.success_rate
        color = 'green' if rate >= 90 else 'orange' if rate >= 70 else 'red'
        return format_html(
            '<span style="color: {};">{}%</span>',
            color, round(rate, 1)
        )
    success_rate_display.short_description = 'Success Rate'


@admin.register(FederationLog)
class FederationLogAdmin(admin.ModelAdmin):
    list_display = [
        'created', 'status_indicator', 'node', 'entry_fqid_short', 
        'response_status_code'
    ]
    list_filter = ['status', 'node', 'created']
    search_fields = ['entry_fqid', 'error_message']
    readonly_fields = [
        'node', 'status', 'entry_fqid', 'request_payload', 
        'response_status_code', 'response_body', 'error_message',
        'created', 'completed'
    ]
    date_hierarchy = 'created'
    
    def has_add_permission(self, request):
        return False  # Logs are created automatically
    
    def status_indicator(self, obj):
        colors = {
            'success': 'green',
            'failure': 'red',
            'pending': 'orange'
        }
        return format_html(
            '<span style="color: {};">●</span>',
            colors.get(obj.status, 'gray')
        )
    status_indicator.short_description = 'Status'
    
    def entry_fqid_short(self, obj):
        if len(obj.entry_fqid) > 50:
            return obj.entry_fqid[:50] + '...'
        return obj.entry_fqid
    entry_fqid_short.short_description = 'Entry FQID'
