from urllib.parse import unquote
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from inbox.models import FollowRequest
from authors.models import Author

def get_follower(author_serial, actor_encoded):
    author = get_object_or_404(Author, serial=author_serial)
    actor_fqid = unquote(actor_encoded)
    actor = get_object_or_404(Author, id=actor_fqid)

    follow_request = FollowRequest.objects.filter(
        actor=foreign_author,
        author_followed=local_author,
        state=FollowRequest.State.ACCEPTED
    ).first()

    if follow_request:
        return {"is_follower": True}
    return None

def add_follower(author_serial, actor_encoded):
    print(author_serial)
    author = get_object_or_404(Author, serial=author_serial)
    actor_fqid = unquote(actor_encoded)
    print(actor_fqid)
    actor = get_object_or_404(Author, id=actor_fqid)

    follow_request = get_object_or_404(FollowRequest,
        actor=actor,
        author_followed=author,
        state=FollowRequest.State.REQUESTING
    )
    follow_request.state = FollowRequest.State.ACCEPTED
    follow_request.save()
    
    return follow_request

def remove_follower(author_serial, actor_encoded):
    author = get_object_or_404(Author, serial=author_serial)
    actor_fqid = unquote(actor_encoded)
    actor = get_object_or_404(Author, id=actor_fqid)

    follow_request = get_object_or_404(
        actor=actor,
        author_followed=author,
        state=FollowRequest.State.ACCEPTED
    )
    follow_request.state = FollowRequest.State.REJECTED
    follow_request.save()
    
    return follow_request