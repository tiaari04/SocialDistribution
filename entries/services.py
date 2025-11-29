from authors.models import Author
from inbox.models import InboxItem, FollowRequest
from federation.models import FederatedNode
from .models import Entry, Comment, Like
from django.utils import timezone
from django.forms.models import model_to_dict
from federation.utils import send_like_to_federation, send_comment_to_federation, sync_remote_authors
from django.utils.dateparse import parse_datetime


def process_federated_public_post(payload: dict) -> dict:
    typ = (payload.get('type') or '').lower()
    
    if typ not in ('post', 'entry'):
        return {'status': 'ignored', 'object': None}
    
    # Ensure author exists
    author_payload = payload.get('author_data') or payload.get('author') or {}
    author = _ensure_author(author_payload)
    if not author:
        return {'status': 'error', 'error': 'missing_author'}

    # fqid can come from 'fqid' or 'id'
    fqid = payload.get('fqid') or payload.get('id')
    if not fqid:
        return {'status': 'error', 'error': 'missing_fqid'}

    # Check if entry exists
    existing_entry = Entry.objects.filter(fqid=fqid).first()
    content_type = payload.get('content_type') or payload.get('contentType') or Entry.ContentType.MARKDOWN
    visibility = payload.get('visibility', Entry.Visibility.PUBLIC)
    
    if existing_entry:
        # Update existing entry
        existing_entry.title = payload.get('title', existing_entry.title)
        existing_entry.content = payload.get('content', existing_entry.content)
        existing_entry.description = payload.get('description', existing_entry.description)
        existing_entry.content_type = content_type
        existing_entry.visibility = visibility
        existing_entry.image_url = payload.get('image_url', existing_entry.image_url)
        existing_entry.is_local = False
        existing_entry.web = payload.get('web', existing_entry.web)
        existing_entry.is_edited = payload.get('is_edited', existing_entry.is_edited)
        existing_entry.save()
        return {'status': 'updated', 'object': existing_entry}

    if payload.get('is_edited'):
        return {'status': 'error', 'error': 'cannot_create_edited_entry'}

    # Create new entry
    entry = Entry.objects.create(
        author=author,
        serial=payload.get('serial') or fqid.split('/')[-1],
        fqid=fqid,
        title=payload.get('title', ''),
        content=payload.get('content', ''),
        description=payload.get('description', ''),
        content_type=content_type,
        visibility=visibility,
        image_url=payload.get('image_url', ''),
        is_local=False,
        web=payload.get('web', ''),
        published=parse_datetime(payload.get('published')) if payload.get('published') else timezone.now(),
    )

    return {'status': 'created', 'object': entry}

def _ensure_author(author_payload: dict) -> Author:
    """Create or get an Author from an incoming payload dict."""
    if not author_payload:
        return None

    author_id = author_payload.get('id')
    if not author_id:
        return None

    # Normalize missing slashes
    author_id = author_id.rstrip('/').encode('utf-8').decode('unicode-escape')
    host = author_payload.get('host', '').rstrip('/')

    local_node = FederatedNode.objects.get(is_local=True)

    # Support both /api and /api/
    host_base = host.removesuffix('/api')
    local_base = local_node.base_url.rstrip('/')

    is_local = (host_base == local_base)
    serial = author_payload.get("uuid") or author_id.rstrip("/").split("/")[-1]
    is_approved = not is_local

    # get newest list of authors before checking that they exist
    sync_remote_authors()

    author, _ = Author.objects.get_or_create(
        id=author_id,
        defaults={
            'displayName': author_payload.get("displayName") or author_payload.get("username") or "",
            'host': host,
            'web': author_payload.get('web', ''),
            'github': author_payload.get("github", ""),
            'profileImage': author_payload.get('profileImage', ''),
            'description': author_payload.get("summary", "") or author_payload.get("note", "") or author_payload.get("bio", ""),
            'is_local': is_local,
            'is_approved': is_approved,
            'serial': serial,  
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

    print(payload)
    typ = (payload.get('type') or '').lower()
    print(typ)
    object_fqid = payload.get('id') or payload.get('object')

    InboxItem.objects.create(recipient=recipient, type=typ, object_fqid=object_fqid or '', payload=payload, received_at=timezone.now())
    if typ == 'comment':
        direction = payload.get('direction')
        author_payload = payload.get('author') or {}
        author = _ensure_author(author_payload)

        entry_fqid = payload.get('entry') or payload.get('object')
        if not entry_fqid:
            return {'status': 'error', 'error': 'missing_entry'}

        normalized_entry_fqid = entry_fqid

        if "/authors/" in entry_fqid and "/api/authors/" not in entry_fqid:
            # If so, replace the first instance of '/authors/' with '/api/authors/'
            normalized_entry_fqid = entry_fqid.replace("/authors/", "/api/authors/", 1)

        try:
            entry = Entry.objects.get(fqid=normalized_entry_fqid)
        except Entry.DoesNotExist:
            return {'status': 'error', 'error': 'entry_not_found'}

        # Ensure comment has an fqid
        comment_fqid = payload.get('id') or f"{entry.fqid}#comment-{timezone.now().timestamp()}"

        # Handle duplicate
        existing = Comment.objects.filter(fqid=comment_fqid).first()
        if existing:
            return {'status': 'exists', 'object': existing}

        # Create comment locally
        comment = Comment.objects.create(
            fqid=comment_fqid,
            author=author,
            entry=entry,
            content=payload.get('content') or payload.get('comment') or "",
            content_type=payload.get('content_type') or payload.get('contentType') or Entry.ContentType.MARKDOWN,
            published=payload.get('published') or timezone.now(),
            web=payload.get('web', ''),
        )
        comment.save()

        if direction == 'outgoing':
            comment_dict = {
                "fqid": comment.fqid,
                "entry": entry.fqid,
                "content": comment.content,
                "content_type": comment.content_type,
                "published": comment.published,
                "web": comment.web,
                "author_id": str(author.id),
                "likes_count": comment.likes_count,
            }

            from federation.utils import send_comment_to_federation
            send_comment_to_federation(comment_dict)

        return {'status': 'created', 'object': comment}

    if typ == 'like':
        print(payload)
        direction = payload.get('direction')
        object_fqid = payload.get('object_fqid').rstrip('/') or payload.get('object').rstrip('/')
        if not object_fqid:
                return {'status': 'error', 'error': 'missing_object'}
        
        if direction == 'outgoing':
            print("OUTGOING")
            author_payload = payload.get('author') or {}
            author = _ensure_author(author_payload)
            
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
            like.save()
            
            like_dict = model_to_dict(like, fields=['fqid', 'object_fqid'])
            like_dict['author_id'] = str(author.id)
            like_dict['published'] = like.published
            
            from federation.utils import send_like_to_federation
            send_like_to_federation(like_dict)
            
            return {'status': 'created', 'object': like}
        
        elif direction == 'incoming' or direction == "" or not direction:
            print("INCOMING")
            author_payload = payload.get('author') or {}
            author = _ensure_author(author_payload)

            existing = Like.objects.filter(author=author, object_fqid=object_fqid).first()
            if existing:
                return {'status': 'exists', 'object': existing}

            like = Like.objects.create(
                fqid=payload.get('id') or f"{object_fqid}#like-{timezone.now().timestamp()}",
                author=author,
                object_fqid=object_fqid,
                published=payload.get('published') or timezone.now(),
            )
            like.save()

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
     
        # Update or create the entry
        entry, created = Entry.objects.update_or_create(
            fqid=fqid,
            defaults={
                "author": author,
                "serial": payload.get('serial') or fqid.split('/')[-1],
                "title": payload.get('title', ''),
                "content": payload.get('content', ''),
                "description": payload.get('description', ''),
                "content_type": payload.get('contentType') or payload.get('content_type', Entry.ContentType.MARKDOWN),
                "visibility": payload.get('visibility', Entry.Visibility.PUBLIC),
                "image_url": payload.get('image_url', ''),
                "web": payload.get('web', ''),
                "published": payload.get('published') or timezone.now(),
                "is_local": False,
            }            
        )
        entry.is_edited = not created
        entry.save()
        return {'status': 'created', 'object': entry}

    if typ == 'follow' or typ == 'followrequest' or typ == 'followRequest':
        actor_payload = payload.get('actor')
        object_payload = payload.get('object')

        if not actor_payload or not object_payload:
            return {'status': 'error', 'error': 'missing_actor_or_object'}

        actor = _ensure_author(actor_payload)
        author_followed = _ensure_author(object_payload)

        existing_request = FollowRequest.objects.filter(actor=actor, author_followed=author_followed).first()
        if existing_request:
            return {'status': 'exists', 'object': existing_request}
            
        follow_request = None
        if actor.is_local:
            if not author_followed.is_local:
                from inbox.services import send_remote_follow_request
                try:
                    print('sending remote follow req')
                    send_remote_follow_request(actor, author_followed)
                    follow_request = FollowRequest.objects.create(
                        actor=actor,
                        author_followed = author_followed,
                        state=FollowRequest.State.ACCEPTED
                    ) 
                    follow_request.save()
                except Exception as e:
                    print("Failed sending follow:", e)

            else:
                follow_request = FollowRequest.objects.create(
                    actor=actor,
                    author_followed = author_followed,
                    state=FollowRequest.State.REQUESTING
                ) 
                follow_request.save()
                return {'status': 'created', 'object': follow_request}

        else:
            follow_request = FollowRequest.objects.create(
                actor=actor,
                author_followed = author_followed
            )
            return {'status': 'created', 'object': follow_request}

    return {'status': 'ignored', 'object': None}

