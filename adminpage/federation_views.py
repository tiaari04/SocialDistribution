"""
Federation management views for adminpage.
Allows admins to manage federated nodes without accessing Django admin.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from adminpage.models import HostedImage
from federation.utils import send_image_to_federation
from django.views.decorators.http import require_POST
from federation.models import FederatedNode, FederationLog
from federation.utils import get_federation_status
import requests


def federation_dashboard(request):
    """Overview of federation status"""
    status = get_federation_status()
    recent_logs = FederationLog.objects.select_related('node').order_by('-created')[:10]
    
    context = {
        'status': status,
        'recent_logs': recent_logs,
    }
    return render(request, 'adminpage/federation/dashboard.html', context)


def nodes_list(request):
    """List all federated nodes"""
    nodes = FederatedNode.objects.all().order_by('-is_active', 'name')
    
    # Pagination
    paginator = Paginator(nodes, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'nodes': page_obj.object_list,
    }
    return render(request, 'adminpage/federation/nodes_list.html', context)


def node_detail(request, pk):
    """Detail view for a specific node with logs"""
    node = get_object_or_404(FederatedNode, pk=pk)
    logs = node.logs.order_by('-created')[:50]
    
    context = {
        'node': node,
        'logs': logs,
    }
    return render(request, 'adminpage/federation/node_detail.html', context)


def node_create(request):
    """Create a new federated node"""
    if request.method == 'POST':
        try:
            is_local = request.POST.get('is_local') == 'true'
            
            node = FederatedNode.objects.create(
                name=request.POST.get('name'),
                base_url=request.POST.get('base_url'),
                api_version='v1',  # Default
                auth_method=request.POST.get('auth_method', 'none'),
                username=request.POST.get('username', ''),
                password=request.POST.get('password', ''),
                token='',  # Not used for none/basic
                inbox_endpoint='/api/authors/',  # Standard endpoint
                is_active=True,  # Always active when created
                is_bidirectional=True,  # Allow both ways by default
                description='',  # Simplified - not needed
                admin_contact='',  # Simplified - not needed
                is_local=is_local,
            )
            messages.success(request, f'Node "{node.name}" created successfully!')
            print(request.POST.get('username', ''))
            return redirect('adminpage:federation-nodes')
        except Exception as e:
            messages.error(request, f'Error creating node: {str(e)}')
    
    return render(request, 'adminpage/federation/node_form.html')


def node_update(request, pk):
    """Update an existing federated node"""
    node = get_object_or_404(FederatedNode, pk=pk)
    
    if request.method == 'POST':
        try:
            node.name = request.POST.get('name')
            node.base_url = request.POST.get('base_url')
            node.auth_method = request.POST.get('auth_method', 'none')
            node.username = request.POST.get('username', '')
            node.password = request.POST.get('password', '')
            node.save()
            
            messages.success(request, f'Node "{node.name}" updated successfully!')
            return redirect('adminpage:federation-node-detail', pk=node.pk)
        except Exception as e:
            messages.error(request, f'Error updating node: {str(e)}')
    
    context = {
        'node': node,
    }
    return render(request, 'adminpage/federation/node_form.html', context)


@require_POST
def node_delete(request, pk):
    """Delete a federated node"""
    node = get_object_or_404(FederatedNode, pk=pk)
    node_name = node.name
    node.delete()
    messages.success(request, f'Node "{node_name}" deleted successfully!')
    return redirect('adminpage:federation-nodes')


@require_POST
def node_toggle_active(request, pk):
    """Toggle node active status via AJAX"""
    node = get_object_or_404(FederatedNode, pk=pk)
    node.is_active = not node.is_active
    node.save(update_fields=['is_active'])
    
    return JsonResponse({
        'success': True,
        'is_active': node.is_active,
        'message': f'Node {"activated" if node.is_active else "deactivated"}'
    })


@require_POST
def node_test_connection(request, pk):
    """Test connection to a node"""
    node = get_object_or_404(FederatedNode, pk=pk)
    
    try:
        headers = node.get_auth_headers()
        # Try to ping the node (adjust endpoint as needed)
        response = requests.get(
            node.base_url,
            headers=headers,
            timeout=10
        )
        
        success = response.status_code in [200, 201, 204]
        
        return JsonResponse({
            'success': success,
            'status_code': response.status_code,
            'message': f'Connection {"successful" if success else "failed"}',
            'response_text': response.text[:200]
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Connection error: {str(e)}'
        })


def logs_list(request):
    """View federation logs with filtering"""
    logs = FederationLog.objects.select_related('node').order_by('-created')
    
    # Filtering
    node_id = request.GET.get('node')
    status = request.GET.get('status')
    
    if node_id:
        logs = logs.filter(node_id=node_id)
    if status:
        logs = logs.filter(status=status)
    
    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'logs': page_obj.object_list,
        'nodes': FederatedNode.objects.all(),
        'statuses': FederationLog.Status.choices,
        'current_node': node_id,
        'current_status': status,
    }
    return render(request, 'adminpage/federation/logs_list.html', context)


def send_image_to_nodes(request, pk):
    image = get_object_or_404(HostedImage, pk=pk)

    if request.method == "POST":
        node_ids = request.POST.getlist("nodes")
        nodes = FederatedNode.objects.filter(
            id__in=node_ids,
            is_active=True,
            is_local=False,
        )

        results = send_image_to_federation(image, nodes=nodes)

        messages.success(
            request,
            f'Sent image to {results["successful"]} node(s), '
            f'{results["failed"]} failed.'
        )
        return redirect("adminpage:images")
    nodes = FederatedNode.objects.filter(is_active=True, is_local=False)

    context = {
        "image": image,
        "nodes": nodes,
    }
    return render(request, "adminpage/federation/send_image.html", context)