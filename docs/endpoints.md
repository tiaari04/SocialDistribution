# Endpoints reference

This document lists the URL endpoints registered in the project, grouped by app/prefix. It covers both the HTML/web
endpoints and the JSON API endpoints (under `/api/`). For each endpoint the document includes: path, HTTP method(s),
the view that handles it, parameters and a short description/notes.

Notes & conventions

- All API endpoints under the `api/` prefix are listed with the full path as seen by an external client (e.g.
  `/api/authors/...`).
- Where a view returns a simple "not implemented" placeholder or an HttpResponse indicating it's not implemented, that
  is noted.
- Authorization: many API endpoints delegate to utilities such as `resolve_author_from_request` and `can_access_entry`.
  Although some viewsets have `AllowAny` permission, access to a specific resource may still be blocked with 403 if
  `can_access_entry` denies access.

---

## Root / project-level routes (in `socialdistribution/urls.py`)

- GET/any: `/admin/`
  - Django admin site

- `adminpage/` (include): `/adminpage/` -> `adminpage.urls` (see Adminpage section)

- `login/` (include): `/login/` -> `login.urls` (see Login section)

- `` (include): `/` -> `entries.urls` (home/stream/public)

- `authors/` (include): `/authors/` -> `authors.urls` (see Authors section)
- `api/` (include): `/api/` -> `api.urls` (see API section)

- `api/` (include): `/api/` -> `api.urls` (see API section)

---

## Entries (web views) — `entries/urls.py`

- GET: `/stream/<author_serial>/`
  - view: `entries.views.stream_home(request, author_serial)`
  - Description: Render the stream/home page for the specified author. Renders `stream_home.html`. Loads Entry objects
    excluding those with visibility `DELETED`.
  - Template context: `entries` (list), `author` (Author instance)

- GET: `/public/`
  - view: `entries.views.public_entries(request)`
  - Note: Returns HttpResponse("public entries (not implemented)").

- GET/POST (not implemented): `/create/`
  - view: `entries.views.entry_create(request)`
  - Note: Returns HttpResponse("entry create (not implemented)").

- GET: `/entries/<entry_serial>/`
  - view: `entries.views.entry_detail(request, entry_serial)`
  - Note: Currently returns a placeholder HttpResponse.

- GET/POST (not implemented): `/entries/<entry_serial>/edit/`
  - view: `entries.views.entry_edit(request, entry_serial)`

---

## Authors (web views) — `authors/urls.py`

- GET: `/authors/`
  - view: `authors.views.author_list(request)`
  - Description: Renders authors list template `authors/authorList.html` with all Author objects.

- GET/POST (not implemented): `/authors/create/`
  - view: `authors.views.author_create(request)`

- GET: `/authors/<author_serial>/`
  - view: `authors.views.author_detail(request, author_serial)`
  - Description: Render author detail page `authors/authorDetail.html`.

- GET/POST: `/authors/<author_serial>/edit/`
  - view: `authors.views.author_edit(request, author_serial)`
  - Description: Logged-in users only (`@login_required`). Accepts profile image upload or an image URL, updates author
    fields and redirects to `authors:detail` on success.

- GET: `/authors/<author_serial>/entries/`
  - view: `authors.views.author_entries_page(request, author_serial)`
  - Note: Returns HttpResponse placeholder (not implemented)

- GET: `/authors/<author_serial>/followers/`
  - view: `authors.views.author_followers_page(request, author_serial)`
  - Note: Placeholder

- GET: `/authors/<author_serial>/follow-requests/`
  - view: `authors.views.follow_requests_page(request, author_serial)`
  - Description: Renders follow requests page using `FollowRequest` objects for that author.

---

## Login (web views) — `login/urls.py`

- GET/POST: `/login/` (root of the login include)
  - view: `login.views.login_view(request)`
  - Description: GET renders the login form `login/login.html`. POST authenticates; on success redirects to the author's
    stream `entries:stream_home` if the Author exists. Shows error messages for invalid credentials or pending approval.

- GET/POST: `/login/signup/`
  - view: `login.views.signup_view(request)`
  - Description: GET renders signup form. POST uses `CustomSignupForm` to create a Django User and an `Author` (local)
    record, handles optional profile image upload, logs in the user and redirects to the new author's stream.
  - Additional behavior: When the signup form includes a `profileImageFile` upload, the server creates a `HostedImage`
    record for that file (`adminpage.models.HostedImage`) and sets the new `Author.profileImage` to the hosted image
    URL. This aligns signup-uploaded images with admin-hosted images and ensures consistent validation and storage.

Examples — signup with profile image

  ```bash
  curl -X POST \
    -F "username=alice" \
    -F "password1=hunter2" \
    -F "password2=hunter2" \
    -F "profileImageFile=@/path/to/avatar.png" \
    http://127.0.0.1:8000/login/signup/
  ```

JS (FormData):

  ```javascript
  const form = new FormData();
  form.append('username', 'alice');
  form.append('password1', 'hunter2');
  form.append('password2', 'hunter2');
  form.append('profileImageFile', fileInput.files[0]);

  fetch('/login/signup/', { method: 'POST', body: form })
    .then(r => r.json())
    .then(console.log);
  ```

---

## Admin pages (web) — `adminpage/urls.py` / `adminpage.views`

- GET: `/adminpage/` -> `adminpage.views.dashboard(request)`
  - Template: `adminpage/dashboard.html`. Shows counts (images, authors, pending users).

### Images

- GET: `/adminpage/images/` -> `adminpage.views.images_list(request)`
  - Query params: `?q=` optional to filter by filename substring.
  - Renders `adminpage/images_list.html`.

- GET/POST: `/adminpage/images/upload/` -> `adminpage.views.image_upload(request)`
  - POST: expects a `HostedImageForm` file upload. Saves and redirects to images list.

Examples — admin image upload (requires session auth / CSRF)

  ```bash
  curl -X POST \
    -F "file=@/path/to/avatar.png" \
    -F "description=Avatar upload" \
    -b "sessionid=<your_session_cookie>" \
    http://127.0.0.1:8000/adminpage/images/upload/
  ```

JS (FormData, using cookies):

  ```javascript
  const form = new FormData();
  form.append('file', fileInput.files[0]);
  form.append('description', 'Avatar upload');

  fetch('/adminpage/images/upload/', { method: 'POST', credentials: 'include', body: form })
    .then(r => r.json())
    .then(console.log);
  ```

- POST (decorated with require_POST): `/adminpage/images/<pk>/delete/` -> `adminpage.views.image_delete(request, pk)`
  - Deletes the HostedImage and redirects to images list.

### Authors (admin)

- GET: `/adminpage/authors/` -> `adminpage.views.authors_list(request)`
  - Shows active authors by default; supports `?q=` filtering.

- GET/POST: `/adminpage/authors/new/` -> `adminpage.views.author_create(request)`
  - Admin form to create local or remote authors. If local and missing `id`, generates one.

- GET/POST: `/adminpage/authors/<path:pk>/edit/` -> `adminpage.views.author_update(request, pk)`
  - Edit author by primary key (note: PK here is the DB PK or path converter).

- POST (require_POST): `/adminpage/authors/<path:pk>/delete/` -> `adminpage.views.author_delete(request, pk)`
  - Soft-delete: marks `Author.is_active=False` and optionally deactivates linked User.

### Approvals

- GET: `/adminpage/approvals/` -> `adminpage.views.pending_users(request)`
  - List of inactive User accounts pending approval.

- POST: `/adminpage/approvals/<int:user_id>/approve/` -> `adminpage.views.approve_user(request, user_id)`
  - Activates the User and creates (or updates) a linked `Author` record.

- POST: `/adminpage/approvals/<int:user_id>/reject/` -> `adminpage.views.reject_user(request, user_id)`
  - Deletes pending user and any linked Author.

### Public images JSON

- GET: (view present in `adminpage.views`) `/adminpage/public_images_json` (not routed in urls.py by default)
  - Function: `public_images_json(request)` – returns a JSON list of hosted images. Note: there is a function but not
    registered in `adminpage/urls.py` in the repo; include it if a public JSON endpoint is desired.

---

## API endpoints — `api/urls.py` + `entries/api_urls.py` (all are prefixed by `/api/`)

Base note: the `api.views` module contains many `not implemented` stubs. Some endpoints delegate to `entries.api_views`
viewsets which are implemented (comments/likes endpoints).

Prefix: `/api/`

### Authors (API)

- GET/POST/PUT/DELETE: `/api/authors/`
  - view: `api.views.api_authors_list(request)`
  - Note: function exists but currently returns 501 (not implemented).

- GET/PUT/DELETE: `/api/authors/<author_serial>/`
  - view: `api.views.api_author_detail(request, author_serial)` — not implemented (501)

- GET: `/api/authors/<author_serial>/followers/`
  - view: `api.views.api_author_followers(request, author_serial)` — not implemented (501)

- GET/PUT/DELETE: `/api/authors/<author_serial>/followers/<path:foreign_encoded>/`
  - view: `api.views.api_author_follower_detail(request, author_serial, foreign_encoded)`
  - Description / behavior:
    - GET: checks whether a remote actor (decoded `foreign_encoded`) is a follower of the
      `author_serial`. Returns follower info or 404 with `{ "is_follower": False }`.
    - PUT: requires authentication. Only the owner of the author
      (`request.user.author.serial == author_serial`) can add a follower. Returns 201 on created.
    - DELETE: requires authentication and ownership; removes follower and returns 200.
  - Notes: `foreign_encoded` is a URL-encoded FQID (the code `unquote()`s it).
    When GET doesn't find the follower a 404 is returned.

- POST: `/api/authors/<author_serial>/inbox/`
  - view: `api.views.api_author_inbox(request, author_serial)`
  - Behavior: accepts POSTed JSON payloads from remote nodes to deliver items (comments/likes/follows). Validates JSON
    and delegates to `entries.services.process_inbox_for`. If processed returns 201 with status `created` or `exists`,
    200 for `ignored`, or 400 for errors.

### Entries API (delegates to entries.api_views)

All these are available under `/api/` because `api.urls` includes `entries.api_urls` at the root of the `api/` include.

- GET/POST: `/api/authors/<author_serial>/entries/<entry_serial>/comments/`
  - view: `entries.api_views.EntryCommentsViewSet` (list/create)
  - GET: paginated comments for the entry. Pagination: 5 items per page by default (SmallPage). Response: DRF paginated
    format.
  - POST: create a comment. Accepts JSON with fields such as `content` (or `comment`), `content_type`/`contentType`
    (default markdown), `id` (optional fqid), `published`, `web`. Creates Comment and returns serialized Comment with
    201.

- GET/POST: `/api/authors/<author_serial>/entries/<entry_serial>/likes/`
  - view: `entries.api_views.EntryLikesViewSet` (list/create)
  - GET: returns a list-like dict { type: 'likes', count: N, src: [ ... ] }, supports query params `page` and `size`
    (pagination implemented manually).
  - POST: create a like. If the requesting author already liked the object, returns 200 with the existing like;
    otherwise creates and returns 201 with the Like representation.

### FQID-based (global) endpoints

- GET/POST: `/api/entries/<path:entry_fqid>/comments/` and `/api/entries/<path:entry_fqid>/likes/`
  - view: same `EntryCommentsViewSet` / `EntryLikesViewSet` with `entry_fqid` parameter.

- GET/POST: `/api/entries/<path:entry_fqid>/comments/<path:comment_fqid>/likes/`
  - view: `entries.api_views.CommentLikesViewSet` — list/create likes on a comment (FQID based)

- GET/POST: `/api/authors/<author_serial>/entries/<entry_serial>/comments/<path:comment_fqid>/likes/`
  - view: `entries.api_views.CommentLikesViewSet` — comment likes when comment is identified by fqid; supports list and
    create.

### Comment detail & likes

- GET: `/api/authors/<author_serial>/entries/<entry_serial>/comments/<path:comment_fqid>/` (delegated to
  EntryCommentsViewSet)
  - Note: API provides list behaviour for comment listing and individual retrieval is implemented by filtering the list
    view (the viewset is used to serve GET list endpoints and creation).

### Other API stubs in `api.views` (not implemented)

- `/api/entry/*` endpoints for serial vs fqid lookups: `api_entry_by_fqid`, `api_entry_image`, `api_entry_image_fqid`,
  etc. — all return 501 currently.
- `/api/author/*` FQID lookup stubs: `api_author_by_fqid`, `api_author_by_fqid_liked`, `api_author_by_fqid_commented` —
  stubs.
- `/api/stream/` -> `api.views.api_stream` — not implemented (501)
- `/api/public/entries/` -> `api.views.api_public_entries` — not implemented (501)

---

## Authentication & permissions notes

- Many API endpoints use `resolve_author_from_request(request)` to map the incoming request to a local `Author` instance
  (based on cookies, auth headers or similar). Where that returns None, the endpoint may still be public but operations
  that require a local author (e.g. creating likes/comments as an author, or checking ownership) will be denied.
- `entries.api_views` viewsets use `AllowAny` but call `can_access_entry(req_author, entry)` which may return a 403.
- Some admin endpoints are decorated with `@require_POST` to enforce method.

---

Sources

The endpoint list was derived from inspecting `urls.py` and the referenced view modules: `api/views.py`,
`entries/views.py`, `entries/api_views.py`, `authors/views.py`, `adminpage/views.py`, and `login/views.py`.

