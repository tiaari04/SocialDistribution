```markdown
# Entries API — Comments & Likes

This document describes the Comments & Likes API implemented in the `entries` app.

Location (implementation):
- Views: `entries/api_views.py` (DRF ViewSets)
- Serializers: `entries/serializers.py`
- Permissions helper: `entries/permissions.py::can_access_entry`
- Inbox processing: `entries/services.py::process_inbox_for`
- Utilities: `entries/utils.py`
- Tests: `entries/tests.py`

Status
------
- All listed user stories for Comments/Likes are implemented on the backend and covered by unit tests in `entries/tests.py`.

Overview of endpoints
---------------------
The API supports both per-author/serial routes and FQID-based routes. All responses are JSON.

Comments (list/create)
- GET  `/api/authors/{author_serial}/entries/{entry_serial}/comments/` — list comments on entry (paginated).
- POST `/api/authors/{author_serial}/entries/{entry_serial}/comments/` — create a comment on the entry. Requestor must be allowed by `can_access_entry()`.
- GET  `/api/entries/{entry_fqid}/comments/` — list comments by entry FQID.
- POST `/api/entries/{entry_fqid}/comments/` — create comment by entry FQID.

Comment likes
- GET  `/api/authors/{author_serial}/entries/{entry_serial}/comments/{comment_fqid}/likes/` — list likes on a comment.
- POST `/api/authors/{author_serial}/entries/{entry_serial}/comments/{comment_fqid}/likes/` — create a like on a comment.

Entry likes
- GET  `/api/authors/{author_serial}/entries/{entry_serial}/likes/` — list likes on an entry.
- POST `/api/authors/{author_serial}/entries/{entry_serial}/likes/` — create a like for an entry.
- GET  `/api/entries/{entry_fqid}/likes/` — list likes by entry FQID.
- POST `/api/entries/{entry_fqid}/likes/` — create like by entry FQID.

Inbox (remote deliveries)
- POST `/api/authors/{author_serial}/inbox/` — endpoint for remote nodes to POST activity payloads (comments, likes, etc.).
  - The inbox handler persists an `InboxItem` and creates a local `Comment` or `Like` when the payload contains `type: "comment"` or `type: "like"`.
  - Minimal remote `Author` records are created from the payload's `author` object.

Payload examples
----------------
Comment (incoming or creation)

```json
{
  "type":"comment",
  "author":{ "id":"http://node/api/authors/111", "displayName":"Greg" },
  "comment":"Great post!",
  "contentType":"text/markdown",
  "published":"2025-10-18T12:34:56+00:00",
  "id":"http://node/api/authors/111/commented/130",
  "entry":"http://node2/api/authors/222/entries/249"
}
```

Like (incoming or creation)

```json
{
  "type":"like",
  "author":{"id":"http://node/api/authors/111","displayName":"Lara"},
  "published":"2025-10-18T12:34:56+00:00",
  "id":"http://node/api/authors/111/liked/166",
  "object":"http://node2/api/authors/222/entries/249"
}
```

Response shapes
---------------
- Comments list: DRF pagination is used by default. The view returns an array of serialized comments. Use `entries/utils.format_comments_response()` if you want the project-style wrapper with `type: comments`, `count`, `src`.
- Likes list: JSON with `type: likes`, `count`, and `src` (array of like objects).

Authentication and actor identity
---------------------------------
Currently the API accepts a best-effort actor identity in these ways (useful for testing or when auth is not yet integrated):

- HTTP header `X-Author-Id`: a fully-qualified author id (FQID) — the API will try to find a local `Author` with that `id`.
- Query param or request JSON `author_id`.

Why `X-Author-Id` is used now
- It allows local testing and quick integration with frontend or remote nodes without a full auth->author mapping in place.
- It is a temporary bridge: the intended long-term approach is to map `request.user` (Django auth) to an `Author` object. The helper `entries/utils.resolve_author_from_request(request)` is provided to centralize that mapping.

How `X-Author-Id` helps the project
- Quick testing: front-end or curl can send an actor header to simulate an authenticated author.
- Remote nodes: some ActivityPub-like flows include the actor id in the payload; using `X-Author-Id` in internal tests helps reproduce remote behavior.
- Migration to real auth: once an auth integration is in place, implement mapping in `resolve_author_from_request` and remove header reliance.

Permissions & visibility
------------------------
- The `can_access_entry(requesting_author, entry)` helper (in `entries/permissions.py`) enforces visibility:
  - PUBLIC: everyone can view/comment/like.
  - FRIENDS: only the entry owner, their friends (mutual accepted follows) and the comment's author can view comments/likes.
  - UNLISTED: only the owner and recipients listed in `EntryDelivery` may view/comment/like.

Edge cases & notes
------------------
- Idempotent likes: if a local `Author` has already liked an object, subsequent POSTs by the same author will return the existing like (idempotent behavior). The DB has a UniqueConstraint preventing duplicate likes for non-null authors.
- `likes_count` is a denormalized integer on `Entry` and `Comment`. Signals update it on create/delete using atomic F() operations, but if you migrate data or modify likes externally, re-sync may be required.

Testing
-------
- Tests for the user stories live in `entries/tests.py` and were executed locally (the `entries` test suite passed during development).
- The tests validate:
  - comment creation on PUBLIC entries
  - like creation and idempotency
  - friends-only visibility behavior
  - unlisted entry delivery-based access

Frontend guidance (quick)
------------------------
- Show counts on entry previews using the `likes_count` and lazily fetch the full likes list when the user opens the likers modal.
- Fetch comments lazily when the user expands the comments section.
- POST like/comment with optimistic UI updates. Revert if the server returns an error.

Errors
------
- 403 Forbidden: actor not allowed to access the entry.
- 400 Bad Request: malformed inbox payload.
- 404 Not Found: entry/comment/author not found.

Next steps / TODO
-----------------
- Replace `X-Author-Id` header usage with real auth -> `Author` mapping in `entries/utils.resolve_author_from_request`.
- Harden ActivityPub validation for remote payloads in `entries/services.py`.
- Add more comprehensive pagination and response-wrapping to exactly match any required public API spec.

If you want, I can also generate a smaller `examples/api_calls.md` with curl commands that the frontend team can copy.

```
