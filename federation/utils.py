import os
import requests

def send_entry_to_federation(entry):
    friend_nodes = [n.strip() for n in os.getenv("FRIEND_NODES", "").split(",") if n.strip()]
    print(friend_nodes)
    if not friend_nodes:
        return

    
    for node in friend_nodes:
        inbox_url = f"{node}/federation/"
        try:
            response = requests.post(inbox_url, json=entry)
            print(response.status_code)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to send entry to {inbox_url}: {e}")