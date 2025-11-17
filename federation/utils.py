import os
import requests
from authors.models import Author
from datetime import datetime
from django.forms.models import model_to_dict

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
    
    # If author_id is an Author object, extract all its data
    if isinstance(payload["author_id"], Author):
        author = payload["author_id"]
        # Manually extract all author fields
        author_data = {
            "id": str(author.id),
            "serial": author.serial or "",
            "displayName": author.displayName or "",
            "github": author.github or "",
            "host": author.host or "",
            "is_active": author.is_active if hasattr(author, 'is_active') else True,
            "is_admin": author.is_admin if hasattr(author, 'is_admin') else False,
            "is_approved": author.is_approved if hasattr(author, 'is_approved') else False,
            "is_local": author.is_local if hasattr(author, 'is_local') else False,
            "profileImage": author.profileImage or "",
            "description": author.description or "",
            "web": author.web or "",
            "created": author.created.isoformat() if hasattr(author, 'created') and author.created else "",
            "updated": author.updated.isoformat() if hasattr(author, 'updated') and author.updated else "",
        }
        payload["author_id"] = str(author.id)
        payload["author_data"] = author_data 
    
    for node in friend_nodes:
        inbox_url = f"{node}/federation/"
        try:
            response = requests.post(inbox_url, json=payload)
            print(f"Sent to {inbox_url}: {response.status_code}")
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to send entry to {inbox_url}: {e}")