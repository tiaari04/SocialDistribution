from uuid import uuid4
from urllib.parse import urljoin

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from urllib.parse import unquote

from .models import HostedImage
from .forms import HostedImageForm, AuthorForm
from authors.models import Author
from django.core.paginator import Paginator

User = get_user_model()

# --------- Helpers ---------

def build_local_author_id(host_base: str, author_uuid: str | None = None) -> str:
    if not host_base.endswith('/'):
        host_base += '/'
    if author_uuid is None:
        author_uuid = uuid4().hex
    return urljoin(host_base, f"authors/{author_uuid}")

def get_local_host_from_settings() -> str:
    return getattr(settings, "NODE_API_BASE", "http://localhost:8000/api/")

# --------- Dashboard ---------

def dashboard(request):
    total_images = HostedImage.objects.count()
    total_authors = Author.objects.filter(is_active=True).count()
    pending_users = Author.objects.filter(is_approved=False).count()
    return render(request, 'adminpage/dashboard.html', {
        'total_images': total_images,
        'total_authors': total_authors,
        'pending_users': pending_users,
    })

# --------- Images ---------

def images_list(request):
    """
    List hosted images that are flagged as admin-uploaded.
    Optional ?q= filters by file name.
    """
    q = request.GET.get('q', '')
    qs = HostedImage.objects.filter(admin_uploaded=True).order_by('-created_at')
    if q:
        # 'file' holds the relative storage name (e.g., uploads/images/<uuid>.png)
        qs = qs.filter(file__icontains=q)
    return render(request, 'adminpage/images_list.html', {'images': qs, 'q': q})

def image_upload(request):
    """
    Upload a single image. Storage backend (e.g., Cloudinary) provides the public URL.
    Always flags uploaded images as admin_uploaded=True since only admins can access this view.
    """
    if request.method == 'POST':
        form = HostedImageForm(request.POST, request.FILES)
        if form.is_valid():
            img = form.save(commit=False)
            img.uploaded_by = request.user if request.user.is_authenticated else None
            img.admin_uploaded = True  # always mark as admin upload
            img.save()
            return redirect('adminpage:images')
    else:
        form = HostedImageForm()
    return render(request, 'adminpage/image_upload.html', {'form': form})

@require_POST
def image_delete(request, pk):
    img = get_object_or_404(HostedImage, pk=pk)
    img.delete()
    return redirect('adminpage:images')

# --------- Authors ---------

def authors_list(request):
    """
    Display only active authors by default.
    """
    q = request.GET.get('q', '')
    qs = Author.objects.filter(is_active=True).order_by('displayName')
    if q:
        qs = qs.filter(displayName__icontains=q)
    return render(request, 'adminpage/authors_list.html', {'authors': qs, 'q': q})

def author_create(request):
    """
    Admin can create local or remote authors. Local authors auto-generate FQIDs.
    """
    if request.method == 'POST':
        form = AuthorForm(request.POST)
        if form.is_valid():
            author: Author = form.save(commit=False)
            if author.is_local and not author.id:
                host_base = author.host or get_local_host_from_settings()
                author.id = build_local_author_id(host_base)
            author.save()
            if author.user and author.user.is_active != author.is_active:
                author.user.is_active = author.is_active
                author.user.save(update_fields=['is_active'])
            return redirect('adminpage:authors')
    else:
        initial = {
            'is_local': True,
            'host': get_local_host_from_settings(),
            'is_active': True,
        }
        form = AuthorForm(initial=initial)
    return render(request, 'adminpage/author_form.html', {'form': form, 'mode': 'Create'})

def author_update(request, pk):
    """
    Update existing author info.
    """
    author = get_object_or_404(Author, pk=pk)
    if request.method == 'POST':
        form = AuthorForm(request.POST, instance=author)
        if form.is_valid():
            author: Author = form.save(commit=False)
            if author.is_local and not author.id:
                host_base = author.host or get_local_host_from_settings()
                author.id = build_local_author_id(host_base)
            author.save()
            if author.user and author.user.is_active != author.is_active:
                author.user.is_active = author.is_active
                author.user.save(update_fields=['is_active'])
            return redirect('adminpage:authors')
    else:
        form = AuthorForm(instance=author)
    return render(request, 'adminpage/author_form.html', {'form': form, 'mode': 'Update'})

@require_POST
def author_delete(request, pk):
    """
    Soft-delete: mark Author as inactive instead of deleting the record.
    """
    author = get_object_or_404(Author, pk=pk)
    if author.is_active:
        author.is_active = False
        author.save(update_fields=['is_active'])
    # Optional: also deactivate linked User
    if author.user and author.user.is_active:
        author.user.is_active = False
        author.user.save(update_fields=['is_active'])
    return redirect('adminpage:authors')

# --------- Pending User Approvals ---------

def pending_users(request):
    qs = Author.objects.filter(is_approved=False).order_by('created')
    return render(request, 'adminpage/pending_users.html', {'pending': qs})

@require_POST
def approve_user(request, user_id):
    user_id = unquote(user_id).rstrip('/')  # decode and normalize trailing slash
    author = (
        Author.objects.filter(id__in=[user_id, user_id + '/']).first()
        or get_object_or_404(Author, pk=user_id)
    )
    author.is_approved = True
    author.save(update_fields=['is_approved'])
    return redirect('adminpage:pending-users')

@require_POST
def reject_user(request, user_id):
    u = get_object_or_404(User, pk=user_id, is_active=False)
    Author.objects.filter(user=u).delete()
    u.delete()
    return redirect('adminpage:pending-users')



def author_detail(request, pk, tab=None):
    from entries.models import Entry
    pk = unquote(pk).rstrip('/')
    author = (
        Author.objects.filter(id__in=[pk, pk + '/']).first()
        or get_object_or_404(Author, pk=pk)
    )

    # Validate/normalize tab
    valid_tabs = [c for c, _ in Entry.Visibility.choices]
    if tab not in valid_tabs:
        tab = Entry.Visibility.PUBLIC

    # Badge counts per tab
    counts = {
        vis: Entry.objects.filter(author=author, visibility=vis).count()
        for vis in valid_tabs
    }

    # Build tabs collection the template can use directly
    tabs = [
        {"key": vis, "label": vis.title(), "count": counts[vis]}
        for vis in valid_tabs
    ]

    # Current tab queryset + pagination
    qs = Entry.objects.filter(author=author, visibility=tab).order_by('-published')
    page_obj = Paginator(qs, 10).get_page(request.GET.get("page"))

    # Friendly blurb
    tab_blurbs = {
        Entry.Visibility.PUBLIC:   "These are publicly visible posts.",
        Entry.Visibility.FRIENDS:  "Posts visible to accepted friends.",
        Entry.Visibility.UNLISTED: "Unlisted posts (not shown in feeds).",
        Entry.Visibility.DELETED:  "Posts marked as deleted.",
    }

    context = {
        "author": author,
        "tab": tab,
        "tabs": tabs,
        "blurb": tab_blurbs.get(tab, ""),
        "page_obj": page_obj,
    }
    return render(request, "adminpage/author_detail.html", context)