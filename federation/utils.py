import os
import requests

def send_entry_to_federation(entry):
    friend_nodes = [n.strip() for n in os.getenv("FRIEND_NODES", "").split(",") if n.strip()]
    if not friend_nodes:
        return

    entry_data = entry.copy()  # if you want to manipulate before sending
    # include author info
    if "author" in entry_data and isinstance(entry_data["author"], Author):
        author = entry_data["author"]
        entry_data["author"] = {
            "id": author.id,
            "displayName": author.displayName,
            "url": author.url,
        }

    for node in friend_nodes:
        inbox_url = f"{node}/federation/"
        try:
            response = requests.post(inbox_url, json=entry_data)
            print(response.status_code, response.text)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to send entry to {inbox_url}: {e}")

