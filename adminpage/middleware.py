# adminpage/middleware.py
from django.conf import settings
from django.shortcuts import redirect
from django.http import HttpResponseForbidden

def _is_author_admin(user):
    # Logged in, has an Author profile, and the flag is True
    author = getattr(user, "author", None)
    return bool(author and getattr(author, "is_admin", False))

class AuthorAdminOnlyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Protect ONLY the adminpage namespace
        if request.path.startswith('/adminpage/'):
            if not request.user.is_authenticated:
                # send to login and then back after auth
                return redirect(f"{settings.LOGIN_URL}?next={request.get_full_path()}")
            if not _is_author_admin(request.user):
                # show a 403 (or redirect somewhere else if you prefer)
                return HttpResponseForbidden("You are not authorized to view this page.")
        return self.get_response(request)