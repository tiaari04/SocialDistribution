from uuid import uuid4
from urllib.parse import urljoin

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib.auth import get_user_model

from .models import HostedImage
from .forms import HostedImageForm, SignupForm, AuthorForm
from authors.models import Author

User = get_user_model()

# --------- Helpers ---------

def build_local_author_id(host_base: str, author_uuid: str | None = None) -> str:
    """
    Build the Author FQID for local authors, e.g., https://node/api/authors/<uuid>
    Adjust to your actual API prefix if different.
    """
    if not host_base.endswith('/'):
        host_base += '/'
    if author_uuid is None:
        author_uuid = uuid4().hex
    return urljoin(host_base, f"authors/{author_uuid}")

def get_local_host_from_settings() -> str:
    """
    Decide where to get your node base URL (for building Author.id).
    Put your canonical base in settings, .env, or Site model.
    """
    # Example: add in settings.py: NODE_API_BASE = "https://your-node/api/"
    return getattr(settings, "NODE_API_BASE", "http://localhost:8000/api/")

# --------- Admin Dashboard ---------

def dashboard(request):
    total_images = HostedImage.objects.count()
    total_authors = Author.objects.count()
    pending_users = User.objects.filter(is_active=False).count()
    return render(request, 'adminpage/dashboard.html', {
        'total_images': total_images,
        'total_authors': total_authors,
        'pending_users': pending_users,
    })

# --------- Images ---------

def images_list(request):
    q = request.GET.get('q', '')
    qs = HostedImage.objects.all().order_by('-created_at')
    if q:
        qs = qs.filter(alt_text__icontains=q)
    return render(request, 'adminpage/images_list.html', {'images': qs, 'q': q})

def image_upload(request):
    if request.method == 'POST':
        form = HostedImageForm(request.POST, request.FILES)
        if form.is_valid():
            img = form.save(commit=False)
            img.uploaded_by = request.user
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

# --------- Authors (URL PKs) ---------

def authors_list(request):
    q = request.GET.get('q', '')
    qs = Author.objects.all().order_by('displayName')
    if q:
        qs = qs.filter(displayName__icontains=q)
    return render(request, 'adminpage/authors_list.html', {'authors': qs, 'q': q})

def author_create(request):
    """
    For local authors, auto-generate the FQID (Author.id) from settings.NODE_API_BASE.
    If you want to allow manual input for federated/remote authors, allow entering 'id'.
    """
    if request.method == 'POST':
        form = AuthorForm(request.POST)
        if form.is_valid():
            author: Author = form.save(commit=False)
            # If local and 'id' not provided, generate one
            if author.is_local and not author.id:
                host_base = author.host or get_local_host_from_settings()
                author.id = build_local_author_id(host_base)
            # Keep Author.is_active in sync with User.is_active (if a user is attached)
            author.save()
            if author.user and author.user.is_active != author.is_active:
                author.user.is_active = author.is_active
                author.user.save(update_fields=['is_active'])
            return redirect('adminpage:authors')
    else:
        # Provide sensible defaults for local creation
        initial = {
            'is_local': True,
            'host': get_local_host_from_settings(),
            'is_active': True,
        }
        form = AuthorForm(initial=initial)
    return render(request, 'adminpage/author_form.html', {'form': form, 'mode': 'Create'})

def author_update(request, pk):
    author = get_object_or_404(Author, pk=pk)
    if request.method == 'POST':
        form = AuthorForm(request.POST, instance=author)
        if form.is_valid():
            author: Author = form.save(commit=False)
            # If local and somehow id empty (shouldn't be), generate it
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
    author = get_object_or_404(Author, pk=pk)
    author.delete()
    return redirect('adminpage:authors')

# --------- Pending User Approvals ---------

def pending_users(request):
    qs = User.objects.filter(is_active=False).order_by('date_joined')
    return render(request, 'adminpage/pending_users.html', {'pending': qs})

@require_POST
def approve_user(request, user_id):
    u = get_object_or_404(User, pk=user_id, is_active=False)
    u.is_active = True
    u.save(update_fields=['is_active'])
    # Ensure an Author exists and is active (local by default)
    author, created = Author.objects.get_or_create(
        user=u,
        defaults={
            'id': build_local_author_id(get_local_host_from_settings()),
            'host': get_local_host_from_settings(),
            'displayName': u.username,
            'is_local': True,
            'is_active': True,
        }
    )
    if not created:
        if not author.id and author.is_local:
            author.id = build_local_author_id(author.host or get_local_host_from_settings())
        author.is_active = True
        author.save()
    return redirect('adminpage:pending-users')

@require_POST
def reject_user(request, user_id):
    u = get_object_or_404(User, pk=user_id, is_active=False)
    # If you also want to delete any pre-created Author:
    Author.objects.filter(user=u).delete()
    u.delete()
    return redirect('adminpage:pending-users')

# --------- Public endpoints ---------

def public_images_json(request):
    data = [{
        'id': i.id,
        'url': i.url,
        'alt_text': i.alt_text,
        'created_at': i.created_at.isoformat(),
    } for i in HostedImage.objects.filter(is_public=True).order_by('-created_at')]
    return JsonResponse({'images': data})

def signup(request):
    """
    Public signup: create an inactive User and a (inactive) local Author shell.
    Admin will later approve -> activates both.
    """
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user: User = form.save(commit=False)
            user.is_active = False
            user.save()
            # Create inactive local Author shell
            Author.objects.get_or_create(
                user=user,
                defaults={
                    'id': build_local_author_id(get_local_host_from_settings()),
                    'host': get_local_host_from_settings(),
                    'displayName': user.username,
                    'is_local': True,
                    'is_active': False,
                }
            )
            return render(request, 'adminpage/signup_submitted.html')
    else:
        form = SignupForm()
    return render(request, 'adminpage/signup.html', {'form': form})