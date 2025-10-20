from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from inbox.models import FollowRequest

def get_follower(author, actor):
    follow_request = FollowRequest.objects.filter(
        actor=actor,
        author_followed=author,
        state=FollowRequest.State.ACCEPTED
    ).first()

    if follow_request:
        return {"is_follower": True}
    return None

def add_follower(author, actor):
    follow_request = get_object_or_404(FollowRequest,
        actor=actor,
        author_followed=author,
        state=FollowRequest.State.REQUESTING
    )
    follow_request.state = FollowRequest.State.ACCEPTED
    follow_request.save()
    
    return follow_request

def remove_follower(author, actor):
    follow_request = get_object_or_404(FollowRequest,
        actor=actor,
        author_followed=author,
    )
    follow_request.state = FollowRequest.State.REJECTED
    follow_request.save()
    
    return follow_request