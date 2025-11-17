import os
import requests

def send_entry_to_federation(entry):
    friend_nodes = [n.strip() for n in os.getenv("FRIEND_NODES", "").split(",") if n.strip()]
    if not friend_nodes:
        return

    # Build the payload
    payload = {
        "fqid": entry.fqid,
        "serial": entry.serial,
        "title": entry.title,
        "web": entry.web,
        "description": entry.description,
        "content": entry.content,
        "image_url": entry.image_url,
        "content_type": entry.content_type,
        "is_edited": entry.is_edited,
        "likes_count": entry.likes_count,
        "visibility": entry.visibility,
        "published": entry.published.isoformat() if entry.published else None,
        "author": {
            "id": entry.author.id,
            "displayName": entry.author.displayName,
            "url": entry.author.url,
        } if entry.author else None
    }

    # Send to all friend nodes
    for node in friend_nodes:
        inbox_url = f"{node}/federation/"
        try:
            response = requests.post(inbox_url, json=payload)
            print(response.status_code, response.text)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to send entry to {inbox_url}: {e}")
