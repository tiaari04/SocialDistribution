import requests
from authors.models import Author
from datetime import datetime
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import FederatedNode, FederationLog
import logging

logger = logging.getLogger(__name__)

results = {
    "successful": 0,
    "failed": 0,
    "logs": []
}


def send_entry_to_federation(entry):
    active_nodes = FederatedNode.objects.filter(is_active=True)
    
    if not active_nodes.exists():
        return {"successful": 0, "failed": 0, "logs": []}
    
    payload = _build_entry_payload(entry)
    
    for node in active_nodes:
        log_entry = _send_to_node(node, payload, entry.get("fqid"))
        results["logs"].append(log_entry)
        
        if log_entry.status == FederationLog.Status.SUCCESS:
            results["successful"] += 1
        else:
            results["failed"] += 1
    
    logger.info(f"Federation send complete: {results['successful']} successful, {results['failed']} failed")
    return results

def send_like_to_federation(like):
    active_nodes = FederatedNode.objects.filter(is_active=True)
    
    if not active_nodes.exists():
        return {"successful": 0, "failed": 0, "logs": []}

    payload = {
        "id": like.get('fqid'),
        "object_fqid": like.get('object_fqid'),
        "published": like.get('published'),
    }

    try:
        author = get_object_or_404(Author, serial=like.get("author_id").split("/")[-1])
        author_data = _build_author_payload(author)
        payload["author"] = author_data
    except Exception as e:
        logger.error(f"Error building author data: {e}")

    for node in active_nodes:
        inbox_url = f"{node.base_url}/federation/like/"
        log_entry = _send_to_node(node, payload, like.get("fqid"), inbox_url)
        results["logs"].append(log_entry)
        
        if log_entry.status == FederationLog.Status.SUCCESS:
            results["successful"] += 1
        else:
            results["failed"] += 1

    logger.info(f"Federation send complete: {results['successful']} successful, {results['failed']} failed")
    return results

def send_comment_to_federation(comment):
    active_nodes = FederatedNode.objects.filter(is_active=True)
    
    if not active_nodes.exists():
        return {"successful": 0, "failed": 0, "logs": []}

    payload = {
        "id": comment.get('fqid'),
        "content": comment.get('content'),
        "content_type": comment.get('content_type'),
        "entry_id": comment.get('entry_id'),
        "likes_count": comment.get('likes_count'),
        "published": comment.get('published'),
        "web": comment.get('web'),
    }

    try:
        author = get_object_or_404(Author, serial=comment.get("author_id").split("/")[-1])
        author_data = _build_author_payload(author)
        payload["author"] = author_data
    except Exception as e:
        logger.error(f"Error building author data: {e}")

    for node in active_nodes:
        inbox_url = f"{node.base_url}/federation/comment/"
        log_entry = _send_to_node(node, payload, comment.get("fqid"), inbox_url)
        results["logs"].append(log_entry)
        
        if log_entry.status == FederationLog.Status.SUCCESS:
            results["successful"] += 1
        else:
            results["failed"] += 1

    logger.info(f"Federation send complete: {results['successful']} successful, {results['failed']} failed")
    return results


def _build_entry_payload(entry):
    payload = {
        "type": "post",
        "author_id": entry.get("author_id") or "",
        "content": entry.get("content") or "",
        "content_type": entry.get("content_type") or "",
        "created": entry.get("created").isoformat() if isinstance(entry.get("created"), datetime) else entry.get("created") or "",
        "description": entry.get("description") or "",
        "fqid": entry.get("fqid") or "",
        "image_url": entry.get("image_url") or "",
        "is_edited": entry.get("is_edited") if entry.get("is_edited") is not None else False,
        "likes_count": entry.get("likes_count") or 0,
        "published": entry.get("published").isoformat() if isinstance(entry.get("published"), datetime) else entry.get("published") or "",
        "serial": entry.get("serial") or "",
        "title": entry.get("title") or "",
        "updated": entry.get("updated").isoformat() if isinstance(entry.get("updated"), datetime) else entry.get("updated") or "",
        "visibility": entry.get("visibility") or "",
        "web": entry.get("web") or "",
    }
    
    try:
        author = get_object_or_404(Author, serial=entry.get("author_id").split("/")[-1])
        author_data = _build_author_payload(author)
        payload["author_id"] = str(author.id)
        payload["author_data"] = author_data
    except Exception as e:
        logger.error(f"Error building author data: {e}")
    
    return payload

def _build_author_payload(author):
    payload = {
        "id": str(author.id),
        "serial": author.serial or "",
        "displayName": author.displayName or "",
        "github": author.github or "",
        "host": author.host or "",
        "is_active": author.is_active if hasattr(author, 'is_active') else True,
        "is_admin": author.is_admin if hasattr(author, 'is_admin') else False,
        "is_approved": author.is_approved if hasattr(author, 'is_approved') else True,
        "is_local": False,
        "profileImage": author.profileImage or "",
        "description": author.description or "",
        "web": author.web or "",
        "created": author.created.isoformat() if hasattr(author, 'created') and author.created else "",
        "updated": author.updated.isoformat() if hasattr(author, 'updated') and author.updated else "",
    }

    return payload

def _send_to_node(node, payload, entry_fqid, endpoint=None):
    log_entry = FederationLog.objects.create(
        node=node,
        entry_fqid=entry_fqid or "unknown",
        request_payload=payload,
        status=FederationLog.Status.PENDING
    )

    url = node.full_inbox_url
    if endpoint: 
        url = endpoint
    
    try:
        headers = node.get_auth_headers()
        
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        log_entry.response_status_code = response.status_code
        log_entry.response_body = response.text[:5000]
        log_entry.completed = timezone.now()
        
        if response.status_code in [200, 201]:
            log_entry.status = FederationLog.Status.SUCCESS
            node.record_success()
            logger.info(f"Successfully sent to {node.name} ({url})")
        else:
            log_entry.status = FederationLog.Status.FAILURE
            log_entry.error_message = f"HTTP {response.status_code}: {response.text[:500]}"
            node.record_failure()
            logger.warning(f"Failed to send to {node.name}: HTTP {response.status_code}")
        
    except requests.RequestException as e:
        log_entry.status = FederationLog.Status.FAILURE
        log_entry.error_message = str(e)[:1000]
        log_entry.completed = timezone.now()
        node.record_failure()
        logger.error(f"Error sending to {node.name}: {e}")
    
    except Exception as e:
        log_entry.status = FederationLog.Status.FAILURE
        log_entry.error_message = f"Unexpected error: {str(e)}"[:1000]
        log_entry.completed = timezone.now()
        node.record_failure()
        logger.exception(f"Unexpected error sending to {node.name}")
    
    finally:
        log_entry.save()
    
    return log_entry


def get_federation_status():
    """
    Get a summary of federation node statuses.
    
    Returns:
        dict: Summary of all nodes and their health
    """
    nodes = FederatedNode.objects.all()
    
    return {
        "total_nodes": nodes.count(),
        "active_nodes": nodes.filter(is_active=True).count(),
        "nodes": [
            {
                "id": node.id,
                "name": node.name,
                "url": node.base_url,
                "is_active": node.is_active,
                "success_rate": node.success_rate,
                "total_sends": node.total_sends,
                "last_successful_send": node.last_successful_send,
            }
            for node in nodes
        ]
    }