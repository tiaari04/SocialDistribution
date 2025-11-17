import os
import requests
from authors.models import Author
from datetime import datetime

def serialize_entry(entry_data):
    """
    Convert entry dictionary into a JSON-serializable format.
    Handles Author objects, datetime fields, and other non-serializable fields.
    """
    data = entry_data.copy()
    
    if "author" in data and isinstance(data["author"], Author):
        author = data["author"]
        data["author"] = {
            "id": author.id,
            "displayName": author.displayName,
            "url": author.url,
        }
    
    for key, value in data.items():
        if isinstance(value, datetime):
            data[key] = value.isoformat()
 
    
    return data

def send_entry_to_federation(entry):
    friend_nodes = [n.strip() for n in os.getenv("FRIEND_NODES", "").split(",") if n.strip()]
    if not friend_nodes:
        return

    entry_data = serialize_entry(entry)

    for node in friend_nodes:
        inbox_url = f"{node}/federation/"
        try:
            print(entry_data)
            response = requests.post(inbox_url, json=entry_data)
            print(f"Sent to {inbox_url}: {response.status_code}")
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to send entry to {inbox_url}: {e}")
