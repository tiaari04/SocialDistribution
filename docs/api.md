# Project API Reference

This document is the canonical API reference for the project. It documents implemented endpoints (comments, likes,
inbox), the intended behavior for stubbed endpoints, and provides examples and per-field documentation required by the
assignment.

What this doc contains

- When to use each endpoint (when)
- How to call each endpoint (how)
- Why the endpoint exists and any caveats (why / why not)
- Multiple examples per endpoint (JSON, PowerShell curl, JS fetch)
- Per-field documentation (type, example, explanation) for request and response shapes
- Pagination guidance and examples

Conventions

- All API endpoints are under the `/api/` prefix (see `socialdistribution/urls.py`).
- Two path styles are supported:
  - Serial-based: `/api/authors/{author_serial}/entries/{entry_serial}/...` (local integer/slug IDs)
  - FQID-based: `/api/entries/{entry_fqid}/...` (arbitrary fully-qualified identifiers)
- Actor resolution: `entries.utils.resolve_author_from_request(request)` checks, in order: `request.user`, `X-Author-Id`
  header, `author_id` query parameter, then `author` field in JSON body.

Authentication / actor identity

Priority for resolving an actor (used by write endpoints):

1. `request.user` mapped to a local `Author` (if your deployment maps users to authors).
2. `X-Author-Id` HTTP header containing the actor FQID.
3. Query parameter `author_id`.
4. JSON body `author.id` or `author_id`.

Endpoints that change author-scoped resources (e.g. follower `PUT`/`DELETE`) require `request.user.is_authenticated` and
that `request.user.author.serial` matches the path `author_serial`.

Common JSON shapes (request & response field docs)

AuthorRef

- Type: object
- Example:

```json
{
  "id": "https://remote.node/api/authors/bob",
  "displayName": "Bob",
  "host": "https://remote.node/",
  "profileImage": "https://cdn.example/bob.png"
}
```

- Fields:
  - `id` (string) — Example: `https://remote.node/api/authors/bob`. The FQID for the author.
  - `displayName` (string) — Human-readable name.
  - `host` (string / URL) — Origin root for the author.
  - `profileImage` (string / URL) — Avatar URL.

Comment (request)

- Type: object
- Example:

```json
{
  "comment": "Nice post!",
  "contentType": "text/markdown",
  "author": { "id": "https://remote.node/api/authors/bob" }
}
```

- Fields (request):
  - `comment` / `content` (string) — Example: `"Nice post!"`. The comment body. Required when creating a comment.
  - `contentType` / `content_type` (string) — Example: `"text/markdown"`. Optional, indicates MIME type.
  - `id` (string / FQID) — Example: `"https://remote.node/api/comments/c1"`. Optional external FQID for inbox
    deliveries.
  - `published` (string / ISO-8601) — Example: `"2025-10-20T12:00:00Z"`. Optional timestamp; server assigns now when
    omitted.
  - `author` (AuthorRef) — Optional (useful for inbox deliveries or remote authors). If omitted for local users, the
    server may map `request.user`.

Comment (response)

- Type: object (serialized comment)
- Example:

```json
{
  "fqid": "https://local/node/entries/entry1#comment-2025-10-20T12:00:00Z",
  "author": { "id": "https://local/node/api/authors/alice", "displayName": "Alice" },
  "content": "Nice post!",
  "content_type": "text/markdown",
  "published": "2025-10-20T12:00:00Z",
  "entry": "http://local/node/entries/entry1",
  "likes_count": 0
}
```

- Fields (response):
  - `fqid` (string) — Assigned unique FQID for the comment. Use as comment identifier when linking.
  - `author` (AuthorRef) — Author information (local or remote) for display.
  - `content` (string) — Text of the comment.
  - `content_type` (string) — MIME type.
  - `published` (string / ISO-8601) — When the comment was published.
  - `entry` (string / FQID) — The entry the comment belongs to.
  - `likes_count` (integer) — Denormalized count of likes for the comment.

Like (request)

- Type: object
- Example:

```json
{
  "author": { "id": "https://remote.node/api/authors/bob" },
  "object": "http://local/node/entries/entry1"
}
```

- Fields (request):
  - `author` (AuthorRef) — The actor who liked the object. If omitted and your deployment maps `request.user` to an
    `Author`, the server may derive the author.
  - `object` / `object_fqid` (string / FQID) — The FQID/URL of the object being liked (entry or comment). For entry-
    scoped endpoints this can be omitted as the endpoint implies the object.
  - `id` (string / FQID) — Optional external FQID for the like.

Like (response)

- Type: object
- Example:

```json
{
  "fqid": "https://local/node/likes/like1",
  "author": { "id": "https://remote.node/api/authors/bob" },
  "object_fqid": "http://local/node/entries/entry1",
  "published": "2025-10-20T12:01:00Z"
}
```

- Fields (response):
  - `fqid` (string) — Like unique id assigned by server.
  - `author` (AuthorRef) — Actor who created the like.
  - `object_fqid` (string) — Target object FQID.
  - `published` (ISO-8601) — Timestamp created.

Errors & status codes (summary)

- 200 OK — successful GET or idempotent POST returning existing object
- 201 Created — resource created
- 400 Bad Request — invalid payload
- 403 Forbidden — permission denied (owner checks / visibility)
- 404 Not Found — missing resource
- 405 Method Not Allowed — wrong HTTP verb
- 501 Not Implemented — stub endpoint

Pagination

- Comments: DRF PageNumberPagination with page_size = 5. Use `?page=` to iterate pages. Example:
  `/api/authors/alice_serial/entries/entry1/comments/?page=2`.
- Likes: manual pagination via `?page=` and `?size=` (defaults: page=1, size=50). Example:
  `/api/authors/alice_serial/entries/entry1/likes/?page=2&size=25`.

---

## Authors endpoints (short)

These endpoints are largely stubs but are documented for completeness.

### `GET /api/authors/` (stub)

Purpose: list authors. Currently returns 501 Not Implemented.

Example response:

```json
{ "detail": "not implemented", "endpoint": "api_authors_list" }
```

### `GET/PUT/DELETE /api/authors/{author_serial}/followers/{foreign_encoded}/`

Purpose: check or manage whether a URL-encoded foreign actor is a follower of the given author.

- `GET` returns 200 with `{ "is_follower": true }` or 404 with `{ "is_follower": false }`.
- `PUT` and `DELETE` require owner authentication (`request.user.author.serial == author_serial`).

Example (GET):

```http
GET /api/authors/alice_serial/followers/https%3A%2F%2Fnode.example%2Fapi%2Fauthors%2Fbob
```

Example response:

```json
{ "is_follower": true }
```

Per-field docs (follower detail)

- Request (PUT to add follower):

```json
{ "actor": { "id": "https://remote.node/api/authors/bob", "displayName": "Bob" } }
```

- Response (201 Created):

```json
{ "detail": "Follower added" }
```

- Response (DELETE success 200):

```json
{ "detail": "Follower removed" }
```

- Error example (403 Forbidden when not owner):

```json
{ "detail": "Forbidden" }
```

Implemented in: `api.views.api_author_follower_detail` (uses `inbox.services` helpers)

---

## Admin / Public Images API

`GET /adminpage/public_images_json` (note: function exists in `adminpage.views` but is not registered by default in
`adminpage/urls.py`)

Purpose: list hosted images (id, url, created_at). Useful for clients that need to fetch image metadata for entries.

Example response (200 OK):

```json
{
  "images": [
    { "id": "1", "url": "http://cdn.example.com/images/example1.png", "created_at": "2025-10-01T12:00:00Z" }
  ]
}
```

Implemented in: `adminpage.views.public_images_json` (returns `JsonResponse({ 'images': [...] })`)

---

Profile image handling (signup)

- When a user uploads a profile image during signup (the signup form's `profileImageFile`), the application now saves
  that upload as a `HostedImage` record (`adminpage.models.HostedImage`).
- The new `Author` record's `profileImage` field is populated with the hosted file's absolute URL (the
  `HostedImage.file.url` value built into an absolute URL by the server). This makes profile images uploaded at signup
  behave the same as images uploaded via the admin image UI.
- Tests: there is a unit test covering this behavior (example:
  `login.tests.AuthViewTests.test_signup_with_image_creates_hostedimage_and_sets_author_profile`).

Examples — admin image upload & signup with image

Admin image upload (curl)

```bash
curl -X POST \
  -F "file=@/path/to/avatar.png" \
  -F "description=Avatar upload" \
  -b "sessionid=<your_session_cookie>" \
  http://127.0.0.1:8000/adminpage/images/upload/
```

Notes: the admin image upload requires an authenticated session (or CSRF token if using the admin forms). On local dev
you can obtain the `sessionid` cookie by logging in to the site in your browser and copying the cookie value.

Admin image upload (JS — FormData)

```javascript
const form = new FormData();
form.append('file', fileInput.files[0]);
form.append('description', 'Avatar upload');

fetch('http://127.0.0.1:8000/adminpage/images/upload/', {
  method: 'POST',
  credentials: 'include', // include cookies for session auth
  body: form
}).then(r => r.json()).then(console.log).catch(console.error);
```

Signup with profile image (curl multipart)

```bash
curl -X POST \
  -F "username=alice" \
  -F "password1=hunter2" \
  -F "password2=hunter2" \
  -F "profileImageFile=@/path/to/avatar.png" \
  http://127.0.0.1:8000/signup/
```

Signup with profile image (JS — FormData)

```javascript
const form = new FormData();
form.append('username', 'alice');
form.append('password1', 'hunter2');
form.append('password2', 'hunter2');
form.append('profileImageFile', fileInput.files[0]);

fetch('http://127.0.0.1:8000/signup/', {
  method: 'POST',
  body: form
}).then(r => r.json()).then(data => {
  // server will create a HostedImage for the file and return an Author payload
  console.log(data);
});
```

How to verify locally (Django shell)

- Open the Django shell after a successful signup with an uploaded image:

```bash
python manage.py shell
```

- Inspect the latest HostedImage and the created Author.profileImage:

```python
from adminpage.models import HostedImage
from authors.models import Author
print(HostedImage.objects.last().file.url)
print(Author.objects.get(user__username='alice').profileImage)
```

## Inbox endpoint — `POST /api/authors/{author_serial}/inbox/`

When to use

- Remote nodes POST activity payloads (comments, likes, follow requests) targeting a local author.

How to use

- POST a JSON activity with `type` equal to `comment`, `like`, or `follow`.
- The server delegates processing to `entries.services.process_inbox_for` and returns a status object.

Why / notes

- Accepts remote payloads in ActivityStreams-like form. Used for federation/inbox workflows. The server attempts to
  create local Comment/Like/FollowRequest records when appropriate.

Request example (comment delivery):

```json
{
  "type": "comment",
  "id": "https://remote.node/api/comments/c123",
  "author": { "id": "https://remote.node/api/authors/bob", "displayName": "Bob" },
  "comment": "Nice post!",
  "contentType": "text/plain",
  "entry": "http://local/node/entries/entry1",
  "published": "2025-10-20T12:00:00Z"
}
```

PowerShell cURL example (deliver comment):

```powershell
curl -X POST -H "Content-Type: application/json" -d '{"type":"comment","author":{"id":"https://remote.node/api/authors/bob"},"comment":"Nice post!","entry":"http://local/node/entries/entry1"}' https://local/node/api/authors/alice_serial/inbox/
```

JS fetch example:

```javascript
fetch('https://local/node/api/authors/alice_serial/inbox/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ type: 'comment', author: { id: 'https://remote.node/api/authors/bob' }, comment: 'Nice post!', entry: 'http://local/node/entries/entry1' })
}).then(r => r.json()).then(console.log)

Additional inbox delivery examples

PowerShell cURL example (deliver like):

```powershell
curl -X POST -H "Content-Type: application/json" -d '{"type":"like","author":{"id":"https://remote.node/api/authors/bob"
},"object":"http://local/node/entries/entry1","id":"https://remote.node/api/likes/l456"}'
https://local/node/api/authors/alice_serial/inbox/
```

JS fetch example (deliver like):

```javascript
fetch('https://local/node/api/authors/alice_serial/inbox/', { method: 'POST', headers: { 'Content-Type':
'application/json' }, body: JSON.stringify({ type: 'like', author: { id: 'https://remote.node/api/authors/bob' },
object: 'http://local/node/entries/entry1', id: 'https://remote.node/api/likes/l456' }) }).then(r =>
r.json()).then(console.log)
```

PowerShell cURL example (deliver follow request):

```powershell
curl -X POST -H "Content-Type: application/json" -d
'{"type":"follow","actor":{"id":"https://remote.node/api/authors/bob"},"object":"https://local/node/api/authors/alice"}'
https://local/node/api/authors/alice_serial/inbox/
```

JS fetch example (deliver follow request):

```javascript
fetch('https://local/node/api/authors/alice_serial/inbox/', { method: 'POST', headers: { 'Content-Type':
'application/json' }, body: JSON.stringify({ type: 'follow', actor: { id: 'https://remote.node/api/authors/bob' },
object: 'https://local/node/api/authors/alice' }) }).then(r => r.json()).then(console.log)
```

Implemented in: `api.views.api_author_inbox` (delegates to `entries.services.process_inbox_for`)

Responses (examples)

- 201 Created — { "detail": "ok", "status": "created" }
- 201 Created — { "detail": "ok", "status": "exists" } (duplicate)
- 200 OK — { "detail": "ignored" } (type not handled)
- 400 Bad Request — { "detail": "error", "error": "..." }

Field-level notes:

- For inbox deliveries include `author` (AuthorRef) so remote actor details are persisted.
- Include `entry` (FQID) for comment/like deliveries so the server can link the item to the correct entry.

---

## Entries — comments & likes

All the implemented endpoints for comments and likes are described below. Both serial and FQID-based
routes are supported. Examples show the serial-based route.
The FQID route is functionally identical but accepts a fully-qualified path in the URL.

### `GET/POST /api/authors/{author_serial}/entries/{entry_serial}/comments/`

When to use: list comments or post a new comment on an entry.

How to use (create): send JSON with `comment` (or `content`) and optional `contentType`, `id`, `published`, and `author`.

Why/notes: the endpoint enforces entry visibility via `can_access_entry`.
Comments created locally get an assigned `fqid` and a `published` timestamp if omitted.

Request example (create):

```json
{ "comment": "Great article!", "contentType": "text/markdown" }
```

PowerShell cURL example:

```powershell
curl -X POST -H "Content-Type: application/json" -d '{"comment":"Great article!","contentType":"text/markdown"}'
https://local/node/api/authors/alice_serial/entries/entry1/comments/
```

JS fetch example:

```javascript
fetch('https://local/node/api/authors/alice_serial/entries/entry1/comments/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ comment: 'Great article!', contentType: 'text/markdown' })
})
  .then(r => r.json())
  .then(console.log)
```

Response (201 created) — example and field explanations are located in the Comment (response) section above.

Pagination: DRF PageNumberPagination with page_size=5. Example page request: `?page=2`.

Errors: 403 when `can_access_entry` denies access, 400 for malformed JSON.

Implemented in: `entries.api_views.EntryCommentsViewSet` (uses `SmallPage` DRF PageNumberPagination)

Sample paginated GET response (comments):

```json
{
  "count": 12,
  "next": "https://local/node/api/authors/alice_serial/entries/entry1/comments/?page=3",
  "previous": "https://local/node/api/authors/alice_serial/entries/entry1/comments/?page=1",
  "results": [
    {
      "fqid": "https://local/node/entries/entry1#comment-1",
      "author": { "id": "https://local/node/api/authors/alice", "displayName": "Alice" },
      "content": "Great article!",
      "content_type": "text/markdown",
      "published": "2025-10-20T12:00:00Z",
      "entry": "http://local/node/entries/entry1",
      "likes_count": 2
    }
  ]
}
```

### `GET/POST /api/authors/{author_serial}/entries/{entry_serial}/likes/`

When to use: list likes on an entry or create a like.

How to use (create): POST JSON with `author` (AuthorRef) or rely on server to derive author from `request.user`/X-Author-Id.

Idempotency: creating a like for the same local actor on the same object is idempotent.
If the like already exists the server returns 200 with the existing Like; otherwise it creates one and returns 201.

Request example (create):

```json
{ "author": { "id": "https://remote.node/api/authors/bob" } }
```

PowerShell cURL example:

```powershell
curl -X POST -H "Content-Type: application/json" -d '{"author":{"id":"https://remote.node/api/authors/bob"}}'
https://local/node/api/authors/alice_serial/entries/entry1/likes/
```

JS fetch example:

```javascript
fetch('https://local/node/api/authors/alice_serial/entries/entry1/likes/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ author: { id: 'https://remote.node/api/authors/bob' } })
})
  .then(r => r.json())
  .then(console.log)
```

List response example (likes):

```json
{ "type": "likes", "count": 2, "src": [
    {
      "fqid": "https://local/node/likes/l1",
      "author": { "id": "https://a/" }
    }
] }
```

Pagination: manual `?page=` and `?size=` params (defaults: page=1, size=50).

Implemented in: `entries.api_views.EntryLikesViewSet` (manual pagination via `page` and `size` query params)

Sample paginated GET response (likes, page=2,size=25):

```json
{ "type": "likes", "count": 125, "src": [
    { "fqid": "https://local/node/likes/l45", "author": { "id": "https://remote.node/api/authors/bob" }, "object_fqid": "http://local/node/entries/entry1", "published": "2025-10-20T12:01:00Z" }
] }
```

---

### FQID-based endpoints

Replace serial-based path with the FQID-encoded path when you have a fully-qualified entry id. Examples:

- `POST /api/entries/{entry_fqid}/comments/`
- `POST /api/entries/{entry_fqid}/likes/`

When posting to these endpoints include the same JSON bodies as the serial-based variants.

---

### Comment likes (comment-scoped)

`GET/POST /api/authors/{author_serial}/entries/{entry_serial}/comments/{comment_fqid}/likes/`

`GET/POST /api/entries/{entry_fqid}/comments/{comment_fqid}/likes/`

Purpose: list/create likes for a specific comment. Uses the same like create semantics and idempotency rules described earlier.

---

Implemented in: `entries.api_views.CommentLikesViewSet`

## Misc / stub endpoints (short)

- `/api/stream/` — intended global/aggregated stream (501 currently).
- `/api/public/entries/` — intended public entries list (501 currently).
- Entry image endpoints (stubs): `/api/authors/{author_serial}/entries/{entry_serial}/image/` and `/api/entries/{entry_fqid}/image/`.
- Other FQID lookup helpers are present as stubs and return 501.

Admin helper

- `adminpage.views.public_images_json(request)` returns a JSON list of hosted images (not registered by default).
