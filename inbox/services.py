from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from inbox.models import FollowRequest
from inbox.serializers import serialize_follow_req
import requests
from requests.auth import HTTPBasicAuth

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

    try:
        send_remote_follow_request(author, actor)

        follow_request = FollowRequest.objects.create(
            actor=author,
            author_followed = actor,
            state=FollowRequest.State.ACCEPTED
        ) 
        follow_request.save()
    except Exception as e:
        print("Failed sending follow:", e)
    
    return {"details": "created"}

def remove_followed_author(author, actor):
    try:
        follow_request = FollowRequest.objects.get(
            actor=author,
            author_followed=actor,
        )
        follow_request.delete()
    except FollowRequest.DoesNotExist:
        print("here1")
        follow_request = None
    
    return follow_request

def send_remote_follow_request(actor, obj):
    data = serialize_follow_req(actor, obj)
    inbox_url = f"{obj.host}authors/{obj.serial}/inbox/"
    resp = requests.post(inbox_url, json=data, timeout=5)
    resp.raise_for_status()