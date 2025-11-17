from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from inbox.models import FollowRequest
from inbox.serializers import serialize_follow_req
import requests

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

def get_followed_author(author, actor):
    follow_request = FollowRequest.objects.filter(
        actor=author,
        author_followed=actor,
        state=FollowRequest.State.ACCEPTED
    ).first()

    if follow_request:
        return {"is_following": True}
    return None

def add_followed_author(author, actor):
    follow_request = FollowRequest.objects.filter(
        actor=author,
        author_followed=actor,
    ).first()

    if follow_request:
        return {"details": "exists"}
    
    if author.host == actor.host:
        follow_request = FollowRequest.objects.create(
            actor=author,
            author_followed = actor,
            state=FollowRequest.State.REQUESTING,
        )
        follow_request.save()
        return {"details": "created"}

    
    follow_request = FollowRequest.objects.create(
        actor=author,
        author_followed = actor,
        state=FollowRequest.State.ACCEPTED
    ) 
    follow_request.save()

    data = serialize_follow_req(author, actor)
    url = f"{actor.id}/inbox"
    resp = requests.post(url, data)
    
    return {"details": "created"}

def remove_followed_author(author, actor):
    try:
        follow_request = FollowRequest.objects.get(
            actor=author,
            author_followed=actor,
        )
        follow_request.delete()
    except FollowRequest.DoesNotExist:
        follow_request = None
    
    return follow_request