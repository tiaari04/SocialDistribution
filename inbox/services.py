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
    follow_request = FollowRequest.objects.filter(
        actor=actor,
        author_followed=author,
    ).first()

    if follow_request and not follow_request.state == FollowRequest.State.ACCEPTED:
        follow_request.state = FollowRequest.State.ACCEPTED
        follow_request.save()
    elif follow_request:
        pass
    
    return follow_request

def remove_follower(author, actor):
    try:
        follow_request = FollowRequest.objects.get(
            actor=actor,
            author_followed=author,
        )
        follow_request.delete()
    except FollowRequest.DoesNotExist:
        follow_request = None

    return follow_request