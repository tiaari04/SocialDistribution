from django.forms import model_to_dict
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse, HttpResponseForbidden
from adminpage.models import HostedImage
from inbox.models import FollowRequest
from .models import Entry
from authors.models import Author
from django.shortcuts import render, redirect, get_object_or_404
from .forms import EntryForm
from django.utils import timezone
from urllib.parse import urlparse
import uuid
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


@csrf_exempt
@require_POST
def github_webhook(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    event = request.headers.get('X-GitHub-Event', '')
    repo = payload.get('repository', {}).get('full_name', '')
    repo_html_url = payload.get('repository', {}).get('html_url', '')
    entries_created = []

    if event == "push":
        commits = payload.get('commits', [])
        for commit in commits:
            github_username = commit.get("author", {}).get("username") or payload.get("pusher", {}).get("name")
            if not github_username:
                continue

            github_url = f"https://github.com/{github_username}".lower()
            try:
                author = Author.objects.get(github__iexact=github_url)
            except Author.DoesNotExist:
                continue
            except Author.MultipleObjectsReturned:
                continue

            message = commit.get('message', '(no message)')
            url = commit.get('url', '')
            author_name = commit.get('author', {}).get('name', github_username)

            content = (f"{author_name} pushed to {repo}: {message}")

            serial = uuid.uuid4().hex[:12]
            fqid = f"{request.build_absolute_uri('/')[:-1]}/authors/{author.serial}/entries/{serial}"

            entry = Entry.objects.create(
                author=author,
                serial=serial,
                title=f"GitHub Activity - {repo}",
                content=content,
                visibility=Entry.Visibility.PUBLIC,
                published=timezone.now(),
                fqid=fqid
            )
            entries_created.append(entry.serial)

    elif event == "pull_request":
        pr = payload.get('pull_request', {})
        github_username = pr.get("user", {}).get("login")
        if not github_username:
            return JsonResponse({'status': 'ignored', 'reason': 'PR user missing'}, status=400)

        github_url = f"https://github.com/{github_username}".lower()
        try:
            author = Author.objects.get(github__iexact=github_url)
        except Author.DoesNotExist:
            return JsonResponse({'status': 'ignored', 'reason': f'No author with GitHub link {github_url}'}, status=404)

        action = payload.get('action')
        title = pr.get('title')
        url = pr.get('html_url')

        content = (f"{author_name} {action} a pull request in {repo}: {title}")

        serial = uuid.uuid4().hex[:12]
        fqid = f"{request.build_absolute_uri('/')[:-1]}/authors/{author.serial}/entries/{serial}"

        entry = Entry.objects.create(
            author=author,
            serial=serial,
            title=f"GitHub Activity - {repo}",
            content=content,
            visibility=Entry.Visibility.PUBLIC,
            published=timezone.now(),
            fqid=fqid
        )
        entries_created.append(entry.serial)
    else:
        return JsonResponse({'status': 'ignored', 'event': event})

    return JsonResponse({'status': 'ok', 'entries_created': entries_created})

def stream_home(request, author_serial):
    current_author = get_object_or_404(Author, serial=author_serial)


    following = FollowRequest.objects.filter(
        actor=current_author, state=FollowRequest.State.ACCEPTED
    ).values_list("author_followed_id", flat=True)

    followers = FollowRequest.objects.filter(
        author_followed=current_author, state=FollowRequest.State.ACCEPTED
    ).values_list("actor_id", flat=True)

    friends = set(following).intersection(followers)


    base_entries = Entry.objects.exclude(visibility=Entry.Visibility.DELETED)


    public_entries = base_entries.filter(visibility=Entry.Visibility.PUBLIC)
    unlisted_entries = base_entries.filter(
        visibility=Entry.Visibility.UNLISTED,
        author_id__in=followers
    )
    friends_entries = base_entries.filter(
        visibility=Entry.Visibility.FRIENDS,
        author_id__in=friends
    )
    own_entries = base_entries.filter(author=current_author)

    entries = (
        public_entries
        | unlisted_entries
        | friends_entries
        | own_entries
    ).select_related("author").order_by("-published")

    return render(request, "stream_home.html", {
        "entries": entries,
        "author": current_author,
    })

def public_entries(request):
    """
    Returns all public entries.
    """
    if request.method == "GET":
        entries = Entry.objects.filter(visibility=Entry.Visibility.PUBLIC).order_by("-published")
        data = [model_to_dict(e) for e in entries]
        return JsonResponse(data, safe=False)
    return HttpResponseNotAllowed(["GET"])

@login_required
def admin_image_picker(request, author_serial):
    get_object_or_404(Author, serial=author_serial)

    qs = HostedImage.objects.filter(admin_uploaded=True).order_by("-created_at")
    paginator = Paginator(qs, 24)
    page_obj = paginator.get_page(request.GET.get("page") or 1)
    next_url = request.GET.get("next", "")
    if next_url:
        p = urlparse(next_url)
        if (p.scheme or p.netloc) and p.netloc != request.get_host():
            next_url = ""

    return render(request, "entries/image_picker.html", {
        "page_obj": page_obj,
        "next": next_url,
    })

@login_required
def entry_create(request, author_serial):
    author = get_object_or_404(Author, serial=author_serial)
    preselected_hosted = None
    hosted_id = request.GET.get("hosted_id") or request.POST.get("hosted_id")
    if hosted_id:
        preselected_hosted = get_object_or_404(HostedImage, pk=hosted_id, admin_uploaded=True)

    if request.method == "POST":
        form = EntryForm(request.POST, request.FILES or None)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.author = author
            entry.serial = uuid.uuid4().hex[:12]
            scheme = 'https' if request.is_secure() else 'http'
            domain = request.get_host()
            entry.fqid = f"{scheme}://{domain}/authors/{author.serial}/entries/{entry.serial}"
            hosted_id = request.POST.get("hosted_id")
            if hosted_id:
                hosted = get_object_or_404(HostedImage, pk=hosted_id, admin_uploaded=True)
                entry.image_url = request.build_absolute_uri(hosted.file.url)
            elif 'image_file' in request.FILES:
                uploaded_file = request.FILES['image_file']
                hosted = HostedImage(file=uploaded_file, uploaded_by=request.user, admin_uploaded=True)
                hosted.save()
                entry.image_url = request.build_absolute_uri(hosted.file.url)

            entry.published = timezone.now()
            entry.save()
            return redirect("entries:stream_home", author_serial=author.serial)
    else:
        form = EntryForm()

    return render(request, "entries/entry_form.html", {
        "form": form,
        "author": author,
        "preselected_hosted": preselected_hosted,  # for preview + hidden input
    })

def entry_detail(request, author_serial, entry_serial):

    author = get_object_or_404(Author, serial=author_serial)
    entry = get_object_or_404(Entry, author=author, serial=entry_serial)

    # no one can see deleted posts
    if entry.visibility == Entry.Visibility.DELETED:
        return HttpResponseForbidden("This post has been deleted.")

    # everyone can see public posts
    if entry.visibility == Entry.Visibility.PUBLIC:
        return render(request, "stream_home.html", {"entries": [entry], "author": author})
    
    # if you have the link you can see unlisted posts
    if entry.visibility == Entry.Visibility.UNLISTED:
        return render(request, "stream_home.html", {"entries": [entry], "author": author})

    # you can always see your own posts

    if request.user.is_authenticated:
        viewer = request.user.author
        if viewer == author:
            return render(request, "stream_home.html", {"entries": [entry], "author": author})

        follows = FollowRequest.objects.filter(actor=viewer, author_followed=author, state=FollowRequest.State.ACCEPTED).exists()
        followed_by = FollowRequest.objects.filter(actor=author, author_followed=viewer, state=FollowRequest.State.ACCEPTED).exists()

        # friends can see friends-only posts -> requires you to be logged in
        if entry.visibility == Entry.Visibility.FRIENDS:
            if follows and followed_by:
                return render(request, "stream_home.html", {"entries": [entry], "author": author})
            return HttpResponseForbidden("You must be friends with this author to view this post.")
    else:
        return render(request, "stream_home.html", {"entries": [], "author": author})

        
@login_required
def entry_edit(request, author_serial, entry_serial):
    entry = get_object_or_404(Entry, serial=entry_serial, author__serial=author_serial)

    if request.user != entry.author.user:
        return HttpResponse("You do not have permission to edit this post.", status=403)

    # If we arrived from the picker, show what was chosen (template already has the hidden input)
    preselected_hosted = None
    hosted_id_from_get = request.GET.get("hosted_id")
    if hosted_id_from_get:
        preselected_hosted = get_object_or_404(HostedImage, pk=hosted_id_from_get, admin_uploaded=True)

    if request.method == "POST":
        form = EntryForm(request.POST, request.FILES, instance=entry)
        if form.is_valid():
            entry = form.save(commit=False)

            # 1) Remove image if requested
            if request.POST.get("remove_image"):
                entry.image_url = None

            else:
                # 2) If a hosted admin image was selected, prefer that
                hosted_id = request.POST.get("hosted_id")
                if hosted_id:
                    hosted = get_object_or_404(HostedImage, pk=hosted_id, admin_uploaded=True)
                    entry.image_url = request.build_absolute_uri(hosted.file.url)

                # 3) Otherwise, if a new file was uploaded, use it
                elif 'image_file' in request.FILES:
                    uploaded_file = request.FILES['image_file']
                    hosted = HostedImage(file=uploaded_file, uploaded_by=request.user, admin_uploaded=True)
                    hosted.save()
                    entry.image_url = request.build_absolute_uri(hosted.file.url)

            entry.save()
            return redirect("entries:stream_home", author_serial=entry.author.serial)
    else:
        form = EntryForm(instance=entry)

    return render(
        request,
        "entries/entry_edit.html",
        {"form": form, "entry": entry, "preselected_hosted": preselected_hosted},
    )

@login_required
def entry_delete(request, author_serial, entry_serial):
    entry = get_object_or_404(Entry, serial=entry_serial, author__serial=author_serial)
    if request.method == "POST":
        entry.mark_deleted()
        return redirect("entries:stream_home", author_serial=author_serial)
    
    return redirect("entries:entry_edit", author_serial=author_serial, entry_serial=entry_serial)
