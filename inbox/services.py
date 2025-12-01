from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from inbox.models import FollowRequest
from federation.models import FederationLog, FederatedNode
import requests
from requests.auth import HTTPBasicAuth
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

def get_follower(author, actor):
    follow_request = FollowRequest.objects.filter(
        actor=actor,
        author_followed=author,
        state=FollowRequest.State.ACCEPTED
    ).first()

    if follow_request:
        return {"is_follower": True}
    return None

def add_follower(author, actor):
    follow_request = FollowRequest.objects.filter(
        actor=actor,
        author_followed=author,
    ).first()

    if follow_request and not follow_request.state == FollowRequest.State.ACCEPTED:
        follow_request.state = FollowRequest.State.ACCEPTED
        follow_request.save()
    elif follow_request:
        pass
    
    return follow_request

def remove_follower(author, actor):
    try:
        follow_request = FollowRequest.objects.get(
            actor=actor,
            author_followed=author,
        )
        follow_request.delete()
    except FollowRequest.DoesNotExist:
        follow_request = None

    return follow_request

def get_followed_author(author, actor):
    follow_request = FollowRequest.objects.filter(
        actor=author,
        author_followed=actor,
        state=FollowRequest.State.ACCEPTED
    ).first()

    if follow_request:
        return {"is_following": True}
    return None

def add_followed_author(author, actor):
    follow_request = FollowRequest.objects.filter(
        actor=author,
        author_followed=actor,
    ).first()

    if follow_request:
        return {"details": "exists"}

    if author.host == actor.host:
        follow_request = FollowRequest.objects.create(
            actor=author,
            author_followed=actor,
            state=FollowRequest.State.REQUESTING,
        )
        follow_request.save()
        return {"details": "created"}
    else: 
        follow_request = FollowRequest.objects.create(
            actor=author,
            author_followed=actor,
            state=FollowRequest.State.ACCEPTED,
        )
        follow_request.save()
        send_remote_follow_request(author, actor)

    return {"details": "created"}

def remove_followed_author(author, actor):
    try:
        follow_request = FollowRequest.objects.get(
            actor=author,
            author_followed=actor,
        )
        follow_request.delete()
    except FollowRequest.DoesNotExist:
        follow_request = None
    
    return follow_request

def send_remote_follow_request(actor, obj):
    data = serialize_follow_req_with_actor(actor, obj)
    data["type"] = "follow"
    # inbox_url = obj.host.rstrip("/") + f"/authors/{obj.serial}/inbox/"
    # print(obj.host)

    base_url = obj.host.rstrip("/")

    if base_url.endswith("/api"):
        base_url = base_url[:-4]   # remove /api
    elif base_url.endswith("/api/"):
        base_url = base_url[:-5]   # remove /api/

    inbox_url = base_url + f"/api/authors/{obj.serial}/inbox/"
    print('target url:', inbox_url)
    
    node = FederatedNode.objects.get(base_url=base_url)

    log_entry = FederationLog.objects.create(
        node=node,
        entry_fqid=data['summary'],
        request_payload=data,
        status=FederationLog.Status.PENDING
    )
    
    try:
        local_node = FederatedNode.objects.get(is_local=True)
        print(local_node.name)
        print("do we ever get here???????")
        headers = local_node.get_auth_headers()
        # team golden checks for type "follow"
        if "golden" in obj.host: 
            data["type"] = "follow"
            print(data)
        logger.info(f"headers: {headers}")
        
        response = requests.post(
            inbox_url,
            json=data,
            headers=headers,
            timeout=30,
        )
        
        log_entry.response_status_code = response.status_code
        log_entry.response_body = response.text[:5000]
        log_entry.completed = timezone.now()
        
        if response.status_code in [200, 201]:
            log_entry.status = FederationLog.Status.SUCCESS
            node.record_success()
            logger.info(f"Successfully sent to {node.name} ({inbox_url})")
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

def serialize_follow_req_with_actor(actor, obj):
    data = serialize_follow_req(actor, obj) 
    data['actor_data'] = {
        "serial": actor.serial,
        "displayName": actor.displayName,
        "github": actor.github,
        "host": actor.host,
        "is_active": actor.is_active,
        "is_admin": actor.is_admin,
        "is_approved": actor.is_approved,
        "is_local": False,
        "profileImage": actor.profileImage,
        "description": actor.description,
        "web": actor.web,
        "created": actor.created.isoformat() if actor.created else None,
        "updated": actor.updated.isoformat() if actor.updated else None,
    }
    return data


def serialize_follow_req(actor, obj):
    return {
        "type": "follow",  
        "summary": f"{actor.displayName} wants to follow {obj.displayName}",
        "actor": {
            "id": actor.id if hasattr(actor, "id") else f"{actor.host}/authors/{actor.serial}",
            "host": actor.host.replace("\\", ""), 
            "displayName": actor.displayName,
            "github": actor.github or "",
            "profileImage": actor.profileImage or "",
            "web": actor.web or "",
        },
        "object": {
            "type": "author",
            "id": obj.id if hasattr(obj, "id") else f"{obj.host}/authors/{obj.serial}",
            "host": obj.host.replace("\\", ""),  
            "displayName": obj.displayName,
            "github": obj.github or "",
            "profileImage": obj.profileImage or "",
            "web": obj.web or "",
        }
    }