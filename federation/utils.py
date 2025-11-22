import os
import requests
from authors.models import Author
from datetime import datetime
from django.forms.models import model_to_dict
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string

def send_entry_to_federation(entry):
    friend_nodes = [n.strip() for n in os.getenv("FRIEND_NODES", "").split(",") if n.strip()]
    if not friend_nodes:
        return
    
    payload = {
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
    
    author = get_object_or_404(Author, serial=entry.get("author_id").split("/")[-1])
    author_data = {
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
    payload["author_id"] = str(author.id)
    payload["author_data"] = author_data 
    print(author_data)
    
    for node in friend_nodes:
        inbox_url = f"{node}/federation/"
        try:
            response = requests.post(inbox_url, json=payload)
            print(f"Sent to {inbox_url}: {response.status_code}")
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to send entry to {inbox_url}: {e}")

def send_like_to_federation(like):
    friend_nodes = [n.strip() for n in os.getenv("FRIEND_NODES", "").split(",") if n.strip()]
    if not friend_nodes:
        return

    payload = {
        "id": like.get('fqid'),
        "object_fqid": like.get('object_fqid'),
        "published": like.get('published'),
    }

    author = get_object_or_404(Author, serial=like.get("author_id").split("/")[-1])
    author_data = {
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
    payload['author'] = author_data
    for node in friend_nodes:
        inbox_url = f"{node}/federation/like/"
        try:
            response = requests.post(inbox_url, json=payload)
            print(f"Like sent to {inbox_url}: {response.status_code}")
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to send like to {inbox_url}: {e}")

def send_comment_to_federation(comment):
    friend_nodes = [n.strip() for n in os.getenv("FRIEND_NODES", "").split(",") if n.strip()]
    if not friend_nodes:
        return

    payload = {
        "id": comment.get('fqid'),
        "content": comment.get('content'),
        "content_type": comment.get('content_type'),
        "entry_id": comment.get('entry_id'),
        "likes_count": comment.get('likes_count'),
        "published": comment.get('published'),
        "web": comment.get('web'),
    }

    author = get_object_or_404(Author, serial=comment.get("author_id").split("/")[-1])
    author_data = {
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
    payload['author'] = author_data

    for node in friend_nodes:
        inbox_url = f"{node}/federation/comment/"
        try:
            response = requests.post(inbox_url, json=payload)
            print(f"Comment sent to {inbox_url}: {response.status_code}")
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to send comment to {inbox_url}: {e}")

def sync_remote_authors():
    friend_nodes = [n.strip() for n in os.getenv("FRIEND_NODES", "").split(",") if n.strip()]
    for node in friend_nodes:
        fetch_remote_authors(node)

def fetch_remote_authors(remote_base_url):
    LOCAL_NODE_ID = os.getenv("NODE_ID", "").rstrip("/")
    url = f"{remote_base_url.rstrip('/')}/api/authors"
    print("Fetching authors from:", url)

    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
    except Exception as e:
        print("Failed to fetch remote authors:", e)
        return

    data = resp.json()
    authors = data.get("items", [])

    for remote in authors:
        remote_host = remote.get("host", "").rstrip("/")
        if remote_host.startswith(LOCAL_NODE_ID):
            continue

        serial = remote["id"].split("/")[-1]

        Author.objects.update_or_create(
            id=remote["id"],  # remote author's full URL
            defaults={
                "displayName": remote.get("displayName", ""),
                "host": remote.get("host", ""),
                "github": remote.get("github", ""),
                "profileImage": remote.get("profileImage", ""),
                "web": remote.get("web", ""),
                "is_local":False,
                "is_approved":True,
                "serial":serial,
            }
        )

        