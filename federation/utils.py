import os
import requests
from authors.models import Author
from datetime import datetime

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


    if isinstance(payload["author_id"], Author):
        author = payload["author_id"]
        payload["author_id"] = str(author.id)

    for node in friend_nodes:
        inbox_url = f"{node}/federation/"
        try:
            response = requests.post(inbox_url, json=payload)
            print(f"Sent to {inbox_url}: {response.status_code}")
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to send entry to {inbox_url}: {e}")
