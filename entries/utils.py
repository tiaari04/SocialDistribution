"""Small utility helpers for the entries app.

These are lightweight, well-documented helpers intended for reuse across
views/services/tests. They intentionally do not assume a particular auth
backend; they provide best-effort resolution for an `Author` from a request
and helpers to create an Author from an incoming remote payload.
"""
from typing import Optional, Dict
from django.http import HttpRequest
from authors.models import Author


def resolve_author_from_request(request: HttpRequest) -> Optional[Author]:
    """Resolve a best-effort local `Author` object for the incoming request.

    Resolution order:
    - If `request.user` exists and maps directly to an Author via `id` attribute,
      try to look up the Author by a configured mapping (not implemented here).
    - Header `X-Author-Id` (full FQID) if present.
    - Query param or JSON body key `author_id`.

    Returns an `Author` instance or None if none could be resolved.
    """
    # 1. Try request.user -> Author mapping (conservative, optional)
    user = getattr(request, 'user', None)
    if user and getattr(user, 'is_authenticated', False):
        # If you have a mapping from user -> author id, implement it here.
        # Example (pseudo): author_id = getattr(user, 'author_id', None)
        author_id = getattr(user, 'author_id', None)
        if author_id:
            try:
                return Author.objects.get(id=author_id)
            except Author.DoesNotExist:
                pass

    # 2. Header
    header_id = request.headers.get('X-Author-Id') if hasattr(request, 'headers') else None
    if header_id:
        try:
            return Author.objects.get(id=header_id)
        except Author.DoesNotExist:
            return None

    # 3. Query param
    qid = request.GET.get('author_id') if hasattr(request, 'GET') else None
    if qid:
        try:
            return Author.objects.get(id=qid)
        except Author.DoesNotExist:
            return None

    # 4. JSON body (best-effort; body parsing can raise on non-JSON) — avoid side-effects
    try:
        body = request.data if hasattr(request, 'data') else None
    except Exception:
        body = None
    if body and isinstance(body, dict):
        aid = body.get('author_id') or body.get('author', {}).get('id')
        if aid:
            try:
                return Author.objects.get(id=aid)
            except Author.DoesNotExist:
                return None

    return None


def create_author_from_payload(payload: Dict) -> Optional[Author]:
    """Create or get a minimal local `Author` from an incoming author payload.

    Expected payload keys: `id`, `displayName`, `host`, `web`, `profileImage`.
    Returns the `Author` instance or None if payload is missing/invalid.
    """
    if not payload or not isinstance(payload, dict):
        return None
    aid = payload.get('id')
    if not aid:
        return None
    author, _ = Author.objects.get_or_create(
        id=aid,
        defaults={
            'displayName': payload.get('displayName', aid),
            'host': payload.get('host', ''),
            'web': payload.get('web', ''),
            'profileImage': payload.get('profileImage', ''),
            'is_local': False,
        },
    )
    return author


def format_comments_response(queryset, page, size, base_web=None):
    """Return a lightweight wrapper matching the project's comments response shape.

    This helper is intentionally small — callers should pass a prefetched
    queryset page (already sliced) and the helper will assemble the 'comments'
    wrapper containing count and the `src` list if desired.
    """
    total = queryset.count()
    src = [
        {
            'type': 'comment',
            'id': c.fqid,
            'author': {'id': c.author.id if c.author else None, 'displayName': c.author.displayName if c.author else None},
            'comment': c.content,
            'contentType': c.content_type,
            'published': c.published.isoformat(),
            'entry': c.entry.fqid,
            'web': base_web,
            'likes': {'count': c.likes_count},
        }
        for c in page
    ]
    return {'type': 'comments', 'count': total, 'page_number': 1, 'size': size, 'src': src}
