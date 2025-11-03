# User stories → API / feature coverage

This file maps the project user stories to the code and documentation in this repository and gives a concise status for
each story: Implemented, Partial, or Not implemented. It also points to the endpoint(s) and view function(s) that
implement (or partially implement) the story and lists concrete next steps to reach full coverage and per-field API
documentation.

Legend

- Implemented: The feature is implemented end-to-end (UI and/or API) for common use.
- Partial: Core pieces exist (models, views, or API endpoints), but parts are missing (examples, errors, edge-cases, or
  wiring).
- Not implemented: No usable implementation in this sprint.

Notes about scope

- Where functionality is delivered by web views (templates), the document links the view and template where appropriate.
- API endpoints are under `/api/` and are linked to `api` and `entries.api_views` handlers.
- Many "node-to-node" (federation) features are marked Part 3-5; they are out of scope for the current sprint and mostly
  Not implemented.

---

## Identity

1. As an author, I want a consistent identity per node, so that URLs to me/my entries are predictable and don't stop
   working.
   - Status: Implemented (core)
   - Why: Authors have an `id` which is a full FQID (URL), and `Author` model supports `host`, `id`, and `serial`.
   - Implemented in:
     - `authors.models.Author` (model) — primary id fields (see `authors/models.py`)
     - Signup creates Author with full id in `login.views.signup_view` (creates `Author` with `id=f"{domain}/authors/{user.username}"`)
     - Admin create/author helpers in `adminpage.views` ensure FQID generation (`build_local_author_id`).
   - Docs:
     - `docs/api.md` (AuthorRef section)
     - `docs/endpoints.md` (authors web pages and admin helpers)
   - Next steps: add per-field examples (Author create payload and response) to `docs/api.md` and `docs/openapi.yaml`
     for authors endpoints.

2. As a node admin, I want to host multiple authors on my node, so I can have a friendly online community.
   - Status: Implemented (web/admin)
   - Implemented in: `adminpage.views.authors_list`, `adminpage.views.author_create`, `adminpage.views.author_update`
   - Notes: admin UIs are present; API author management endpoints are stubs in `api.views` (501).
   - Next steps: if API-based admin operations are required for grading, add request/response docs or implement the API.

3. As an author, I want a public page with my profile information, so that I can link people to it.
   - Status: Implemented (web)
   - Implemented in: `authors.views.author_detail` (renders `authors/authorDetail.html`)
   - Docs: `docs/endpoints.md` (authors web views)
   - Next steps: add an API author-detail endpoint docs mapping (API detail is a stub in `api.views.api_author_detail` —
     mark 501).

4. As an author, I want my (new, public) GitHub activity to be automatically turned into public entries.
   - Status: Not implemented (out of scope / Part 3-5)
   - Notes: no webhook integration or background worker.

5. As an author, I want my profile page to show my public entries (most recent first).
   - Status: Partial
   - Implemented in: `authors.views.author_detail` (renders a template) and `entries.views.stream_home` (renders a list
     of entries for an author)
   - Notes: templates exist; the data is pulled from `Entry` objects. If grader needs an API endpoint that lists an
     author's entries, `api.views.api_author_entries` is a stub (501).
   - Next steps: add explicit endpoint documentation or implement `api_author_entries` if needed.

6. As an author, I want to be able to edit my profile: name, description, picture, and GitHub.
   - Status: Implemented (web)
   - Implemented in: `authors.views.author_edit` (form handling + file upload support)
   - Docs: `docs/endpoints.md` references the web views; API author edit is currently 501 (api_author_detail).
     - Next steps: add example form parameters and a short API mapping if you want an API-based profile edit documented.
         - Note: Signup/profile image handling was improved.
             When users upload a profile image at signup the server creates a `HostedImage` and sets
             `Author.profileImage` to the hosted file's absolute URL. This makes signup-uploaded images
             behave the same as admin-hosted images.
             A unit test was added to cover this: `login.tests.AuthViewTests.test_signup_with_image_creates_hostedimage_and_sets_author_profile`.

7. As an author, I want to be able to use my web browser to manage my profile.
   - Status: Implemented (web)
   - Implemented in: `authors.views.author_edit`, `login.views.signup_view`, `login.views.login_view`

---

## Posting

8. As an author, I want to make entries, so I can share my thoughts and pictures with other local authors.
   - Status: Not implemented (web entry creation is stubbed)
   - Why: `entries.views.entry_create` returns "not implemented".
   - Next steps: implement web form + API for entry create; document API fields (content, content_type, title, images,
     visibility). Add examples in `docs/api.md` and `openapi.yaml`.

9. As an author, I want my node to send my entries to my remote followers and friends.
   - Status: Not implemented / Part 3-5

10. As an author, I want to edit my entries locally.
    - Status: Not implemented (web edit is stubbed)
    - Why: `entries.views.entry_edit` returns not implemented.
    - Next steps: implement and document edit APIs and web forms; add examples.

11. As an author, I want my node to re-send entries I've edited to everywhere they were already sent.
    - Status: Not implemented / Part 3-5

12. As an author, entries I make can be in CommonMark.
    - Status: Partial/Implemented (model support)
    - Why: `Entry.ContentType` includes `text/markdown` and the serializer/model `content_type` supports it.
    - Implemented in: `entries.models.Entry` (ContentType), `entries.api_views` (create handles contentType)

13. As an author, entries I make can be plain text.
    - Status: Implemented (model support)
    - Implemented in: `entries.models.Entry` and serializers

14. As an author, entries I create can be images.
        - Status: Partial
        - Implemented in: Admin `image_upload` and the `HostedImage` model. Template and admin UI exist.
            Entry image endpoints are stubbed in `api.views` (501).
        - Next steps: add API image upload documentation and link to `adminpage.views.image_upload` if the
            grader expects an API.

15. As an author, entries I create that are in CommonMark can link to images.
    - Status: Partial — possible via `content` referencing hosted images; models permit web/image URLs.

16. As an author, I want to delete my own entries locally.
    - Status: Partial/Not implemented (model supports visibility DELETED; UI/API removal not fully present)
    - Notes: `Entry.mark_deleted` exists; but no web/API endpoint for deletion is implemented.

17. As an author, I want my node to re-send deleted entries (Part 3-5)
    - Status: Not implemented / Part 3-5

18. As an author, I want to use my web-browser to manage/author entries.
    - Status: Partial — stream and detail pages exist; create/edit endpoints are stubs.

19. As an author, other authors cannot modify my entries.
    - Status: Partially implemented (ownership enforced in views/permissions)
        - Implemented in: permission checks in `entries.api_views` (e.g. `can_access_entry`) and
            elsewhere. Enforcement for writes depends on `resolve_author_from_request`.

---

## Reading (stream)

20. As an author, I want a "stream" which shows all the entries I should know about.
    - Status: Partial
        - Implemented in: `entries.views.stream_home` which renders `stream_home.html` and
            excludes `DELETED` entries. The view shows the entries list.
    - Notes: API-level stream endpoint `api.views.api_stream` is a 501 stub.
    - Next steps: add API stream docs or implement `api_stream` if required.

21. Stream sub-requirements (sorting, visibility, edited handling)
    - Status: Partial
        - Implemented pieces: `Entry` model has `published`, `updated`, `visibility`, and ordering.
            `entries.views.stream_home` uses the `published` field for ordering.
        - Next steps: test/review that edited entries update ordering; add explicit doc examples for the
            stream page and API if required.

---

## Visibility

22–30. Visibility stories (public/unlisted/friends-only controls)
    - Status: Partial
        - Implemented in: `entries.models.Entry` (Visibility enum) and `can_access_entry` permission
            logic referenced by API views.
        - Missing: comprehensive API endpoints that change visibility or a full test harness
            demonstrating access rules. Some access enforcement is present in `entries.api_views` (they
            call `can_access_entry`), so reader-facing behaviors are partially enforced.
        - Next steps: document `visibility` field in `docs/api.md` and add example scenarios
            (403 vs 200) for comments/likes on different visibility types.

---

## Sharing

31. As a reader, I can get a link to a public or unlisted entry.
    - Status: Implemented (model & web)
    - Implemented in: entries have `fqid` (URL) stored and `entries.views` includes `entry.fqid` in template context.

32. As a node admin, I want to push images to users on other nodes (Part 3-5)
    - Status: Not implemented / Part 3-5

33. As an author, I should be able to browse the public entries of everyone.
    - Status: Partial
        - Implemented in: `entries.views.public_entries` (returns a placeholder). The web listing is not
            fully implemented. The API public entries endpoint `api.views.api_public_entries` is a 501 stub.
    - Next steps: implement and document public listing endpoints.

---

## Following / Friends

34. As an author, I want to follow local authors.
    - Status: Implemented
        - Implemented in (UI): `authors` views (followRequests template). `adminpage` exposes 
            follower management helpers via `inbox.services` (internal).
        - Implemented in (API): `api.views.api_author_inbox` supports POST and is implemented. 
            Helper function in `entries.services`
        - Docs: `docs/api.md` notes the inbox endpoint behavior; `docs/endpoints.md` documents it.
        - Next steps: add per-field request/response examples for `PUT` follower add and `DELETE` 
            remove in `docs/api.md` and the OpenAPI document.

35. As an author, I want to follow remote authors (Part 3-5)
    - Status: Implemented

36. As an author, I want to be able to approve or deny other authors following me.
    - Status: Implemented
        - Implemented in (UI): `authors.views.follow_requests_page` has accept and deny buttons that 
            fetch the API
        - Implemented in (API): `api.views.api_author_follower_detail` supports GET/PUT/DELETE and is 
            implemented (not a stub). Helper functions `add_follower` and `remove_follower` are implemented 
            in `inbox.services`
        - Docs: `docs/api.md` notes the follower-detail endpoint behavior; `docs/endpoints.md`
            documents it.
        - Next steps: add example PUT payloads for follower add (what remote actor payload looks like) to `docs/api.md` and OpenAPI.

37. As an author, I want to know if I have "follow requests".
    - Status: Implemented
        - Implemented in (UI): `authors.views.author_detail` fetches a count of follow requests from the
            databse and shows the number on the follow request button.
        - Implemented in (API): no dedicated API endpoint returning pending follow requests but they are 
        retrieved in `authors.views.author_detail`.

38. As an author, I want to unfollow authors I am following.
    - Status: Implemented
        - Implemented in (UI): Unfollow button shown on `authors.templates.authors.authorDetails` if that
            author is being followed. It fetches the API endpoint from there.
        - Implemented in (API): `api.views.api_author_follower_detail` supports GET/PUT/DELETE and is 
            implemented (not a stub). Helper function `remove_follower` are implemented 
            in `inbox.services`.
        - Docs: `docs/api.md` notes the follower-detail endpoint behavior; `docs/endpoints.md`
            documents it.

39. As an author, if I am following another author, and they are following me I want us to be considered friends.
    - Status: Implemented
        - Implemented in (UI): Friends list is shown on `authors.templates.followPages.followers` and is rendered
            by `authors.views.author_followers_page`.
        - Implemented in (API): no dedicated API endpoint returning a list of friends but all followers are 
            retrieved in `authors.views.author_followers_page`. `is_friend` function is implemented in 
            authors.models to check if 2 authors are friends.
        - Docs: `docs/api.md` notes the follower-detail endpoint behavior; `docs/endpoints.md`
            documents it.

40. As an author, I want to unfriend other authors by unfollowing them.
    - Status: Implemented
        - Implemented in (UI): Unfollow button shown on `authors.templates.authors.authorDetails` if that
            author is being followed. Clicking it unfollows the author by fetching the API endpoint. 
            Unfriending someone is observed on follower page where that author will move from the followers 
            list to the friends list.
        - Implemented in (API): `api.views.api_author_follower_detail` supports GET/PUT/DELETE and is 
            implemented (not a stub). Helper function `remove_follower` are implemented 
            in `inbox.services`. `is_friend` function is implemented in authors.models to check if 2 authors 
            are friends.
        - Docs: `docs/api.md` notes the follower-detail endpoint behavior; `docs/endpoints.md`
            documents it.

41. As an author, my node will know about my followers, who I am following, and my friends.
    - Status: Implemented
        - Implemented in (UI): Friends and followers list is shown on `authors.templates.followPages.followers` 
            and is rendered by `authors.views.author_followers_page`. Following list is shown on `authors.templates.followPages.following`and is rendered by `authors.views.author_following_page`. Both pages can be accessed
            from `authors/authorDetail.html`.
        - Implemented in (API): no dedicated API endpoint returning a list of friends but all followers are 
            retrieved in `authors.views.author_followers_page`. `is_friend` function is implemented in 
            authors.models to check if 2 authors are friends.
        - Docs: `docs/api.md` notes the follower-detail endpoint behavior; `docs/endpoints.md`
            documents it.

---

## Comments / Likes

44. As an author, I want to comment on entries that I can access.
    - Status: Implemented (API)
        - Implemented in: `entries.api_views.EntryCommentsViewSet` (list/create). Routes are present in
            `entries/api_urls.py` and requests are delegated via `api.views`.
        - Docs: `docs/api.md` has Comment request/response and examples; `docs/openapi.yaml` contains
            Comment paths and schemas.
        - Next steps: add an explicit error example (403 Forbidden) to `docs/api.md`, and produce
            per-field docs in `openapi.yaml` for all comment fields (done). Also add example responses for
            list pages (already added).

45. As an author, I want to like entries that I can access.
    - Status: Implemented (API)
    - Implemented in: `entries.api_views.EntryLikesViewSet` (list/create). Idempotency handled (existing like returns 200).
    - Docs: `docs/api.md` has examples; `docs/openapi.yaml` has Like paths & schemas.
    - Next steps: add canonical error examples (403) to docs.

46. As an author, I want to like comments that I can access.
    - Status: Implemented (API)
    - Implemented in: `entries.api_views.CommentLikesViewSet` (list/create) and `entries/api_urls.py` for routes.
    - Docs: Add examples for comment-like creation and 403/400 error responses to `docs/api.md`.

47. As an author, when someone sends me a public entry I want to see the likes.
    - Status: Implemented (Partial)
    - Why: likes are queryable via EntryLikesViewSet; the inbox delivery handling is implemented as well.

48. Comments on friends-only entries visibility
    - Status: Partial — `can_access_entry` used in viewsets to enforce; test coverage may be incomplete.

---

## Node management & Admin

49. Admin image hosting
    - Status: Implemented (admin pages + image upload)
        - Implemented in: `adminpage.views.images_list`, `adminpage.views.image_upload`, and
            `adminpage.views.public_images_json` (note: the public JSON view is not registered by default in
            `adminpage/urls.py`).
    - Docs: Mentioned in `docs/endpoints.md`.

50. Admin author management and approvals
    - Status: Implemented (admin UIs)
    - Implemented in: views in `adminpage.views` (approve_user, reject_user, author_create/update/delete)
    - Next steps: add API-level docs if required.

51–end: many node-admin stories (Part 3-5) are out of scope and not implemented.