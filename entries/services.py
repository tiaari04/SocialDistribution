from authors.models import Author
from inbox.models import InboxItem, FollowRequest
from .models import Entry, Comment, Like
from django.utils import timezone


def process_federated_public_post(payload: dict) -> dict:
    """Process a public post arriving from federation (no specific recipient needed).
    
    Returns a dict with keys: 'status' (created/exists/error) and 'object' (Entry or None).
    """
    typ = (payload.get('type') or '').lower()
    
    if typ != 'post' and typ != 'entry':
        return {'status': 'ignored', 'object': None}
    
    # Handle incoming federated posts
    author_payload = payload.get('author_data') or payload.get('author') or {}
    author = _ensure_author(author_payload)
    
    if not author:
        return {'status': 'error', 'error': 'missing_author'}
    
    fqid = payload.get('fqid') or payload.get('id')
    if not fqid:
        return {'status': 'error', 'error': 'missing_fqid'}
    
    # Check if entry already exists (idempotent)
    existing_entry = Entry.objects.filter(fqid=fqid).first()
    if existing_entry:
        return {'status': 'exists', 'object': existing_entry}
    
    # Create the entry
    entry = Entry.objects.create(
        author=author,
        serial=payload.get('serial') or fqid.split('/')[-1],
        fqid=fqid,
        title=payload.get('title', ''),
        content=payload.get('content', ''),
        description=payload.get('description', ''),
        content_type=payload.get('content_type', Entry.ContentType.MARKDOWN),
        visibility=payload.get('visibility', Entry.Visibility.PUBLIC),
        image_url=payload.get('image_url', ''),
        web=payload.get('web', ''),
        published=payload.get('published') or timezone.now(),
    )
    return {'status': 'created', 'object': entry}


def _ensure_author(author_payload: dict) -> Author:
    """Create or get an Author from an incoming payload dict."""
    if not author_payload:
        return None
    author_id = author_payload.get('id')
    if not author_id:
        return None
    author, _ = Author.objects.get_or_create(
        id=author_id,
        defaults={
            'displayName': author_payload.get('displayName', author_id),
            'host': author_payload.get('host', ''),
            'web': author_payload.get('web', ''),
            'profileImage': author_payload.get('profileImage', ''),
        }
    )
    return author


def process_inbox_for(recipient_serial: str, payload: dict) -> dict:
    """Process an incoming inbox payload for the local author with serial `recipient_serial`.

    Returns a dict with keys: 'status' (created/ignored/error) and 'object' (Comment/Like or None).
    """
    # Find recipient author by serial
    try:
        recipient = Author.objects.get(serial=recipient_serial)
    except Author.DoesNotExist:
        return {'status': 'error', 'error': 'recipient_not_found'}

    typ = (payload.get('type') or '').lower()
    object_fqid = payload.get('id') or payload.get('object')

    # Persist raw inbox item
    InboxItem.objects.create(recipient=recipient, type=typ, object_fqid=object_fqid or '', payload=payload, received_at=timezone.now())

    if typ == 'comment':
        # Build and persist Comment
        author_payload = payload.get('author') or {}
        author = _ensure_author(author_payload)
        entry_fqid = payload.get('entry')
        if not entry_fqid:
            return {'status': 'error', 'error': 'missing_entry'}
        try:
            entry = Entry.objects.get(fqid=entry_fqid)
        except Entry.DoesNotExist:
            return {'status': 'error', 'error': 'entry_not_found'}

        comment = Comment.objects.create(
            fqid=payload.get('id') or f"{entry.fqid}#comment-{timezone.now().timestamp()}",
            author=author,
            entry=entry,
            content=payload.get('comment') or payload.get('content') or '',
            content_type=payload.get('contentType') or payload.get('content_type') or entry.ContentType.MARKDOWN,
            published=payload.get('published') or timezone.now(),
            web=payload.get('web', ''),
        )
        return {'status': 'created', 'object': comment}

    if typ == 'like':
        author_payload = payload.get('author') or {}
        author = _ensure_author(author_payload)
        object_fqid = payload.get('object')
        if not object_fqid:
            return {'status': 'error', 'error': 'missing_object'}

        # idempotent: if like exists, return existing
        if author:
            existing = Like.objects.filter(author=author, object_fqid=object_fqid).first()
            if existing:
                return {'status': 'exists', 'object': existing}

        like = Like.objects.create(
            fqid=payload.get('id') or f"{object_fqid}#like-{timezone.now().timestamp()}",
            author=author,
            object_fqid=object_fqid,
            published=payload.get('published') or timezone.now(),
        )
        return {'status': 'created', 'object': like}

    if typ == 'post' or typ == 'entry':
        # Handle incoming federated posts
        author_payload = payload.get('author_data') or payload.get('author') or {}
        author = _ensure_author(author_payload)
        
        if not author:
            return {'status': 'error', 'error': 'missing_author'}
        
        fqid = payload.get('fqid') or payload.get('id')
        if not fqid:
            return {'status': 'error', 'error': 'missing_fqid'}
        
        # Check if entry already exists (idempotent)
        existing_entry = Entry.objects.filter(fqid=fqid).first()
        if existing_entry:
            return {'status': 'exists', 'object': existing_entry}
        
        # Create the entry
        entry = Entry.objects.create(
            author=author,
            serial=payload.get('serial') or fqid.split('/')[-1],
            fqid=fqid,
            title=payload.get('title', ''),
            content=payload.get('content', ''),
            description=payload.get('description', ''),
            content_type=payload.get('content_type', Entry.ContentType.MARKDOWN),
            visibility=payload.get('visibility', Entry.Visibility.PUBLIC),
            image_url=payload.get('image_url', ''),
            web=payload.get('web', ''),
            published=payload.get('published') or timezone.now(),
        )
        return {'status': 'created', 'object': entry}

    if typ == 'follow':
        actor_payload = payload.get('actor')
        object_payload = payload.get('object')

        if not actor_payload or not object_payload:
            return {'status': 'error', 'error': 'missing_actor_or_object'}

        actor = _ensure_author(actor_payload)
        author_followed = _ensure_author(object_payload)

        existing_request = FollowRequest.objects.filter(actor=actor, author_followed=author_followed).first()
        if existing_request:
            return {'status': 'exists', 'object': existing_request}

        follow_request = FollowRequest.objects.create(
            actor=actor,
            author_followed = author_followed
        )
        return {'status': 'created', 'object': follow_request}

    return {'status': 'ignored', 'object': None}
