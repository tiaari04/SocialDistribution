from authors.models import Author
from .models import Entry, EntryDelivery


def can_access_entry(requesting_author: Author | None, entry: Entry) -> bool:
    # Public is always accessible
    if entry.visibility == Entry.Visibility.PUBLIC:
        return True
    # owner can always access
    if requesting_author and requesting_author.id == entry.author.id:
        return True
    # friends
    if entry.visibility == Entry.Visibility.FRIENDS and requesting_author:
        return requesting_author.is_friend(entry.author)
    # unlisted: must be a delivered recipient
    if entry.visibility == Entry.Visibility.UNLISTED and requesting_author:
        return EntryDelivery.objects.filter(entry=entry, recipient_author_fqid=requesting_author.id).exists()
    return False
