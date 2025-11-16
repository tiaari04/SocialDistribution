from django.core import serializers
from authors.models import Author
from inbox.models import FollowRequest

def serialize_followers_view(author, typ):
    followers = []
    resp_type = ''

    if typ == 1:
        followers = FollowRequest.objects.filter(author_followed=author, state=FollowRequest.State.ACCEPTED).select_related('actor')
        resp_type = 'followers'

    elif typ == 2:
        followers = FollowRequest.objects.filter(author_followed=author, state=FollowRequest.State.REQUESTING).select_related('actor')
        resp_type = 'follow requests'

    elif typ == 3:
        followers = FollowRequest.objects.filter(actor=author, state=FollowRequest.State.ACCEPTED).select_related('author_followed')
        resp_type = 'following'

    data = []
    for follow_request in followers:
        if typ == 3:
            author_data = follow_request.author_followed
        else:
            author_data = follow_request.actor

        data.append({
            'type': 'author',
            'id': author_data.id,
            'host': author_data.host,
            'displayName': author_data.displayName,
            'web': author_data.web,
            'github': author_data.github,
            'profileImage': author_data.profileImage
        })

    resp = {'type':resp_type, 'followers':data}
    return resp, 200

def serialize_follow_req(author, obj):
    data = {
        "type": "follow",      
        "summary": f"{author.displayName} wants to follow {obj.displayName}",
        "actor":{
            "type":"author",
            "id":author.id,
            "host":author.host,
            "displayName":author.displayName,
            "github": author.github,
            "profileImage": author.profileImage,
            "web": author.web
        },
        "object":{
            "type":"author",
            "id":obj.id,
            "host":obj.host,
            "displayName":obj.displayName,
            "github": obj.github,
            "profileImage": obj.profileImage,
            "web": obj.web
        }
    }
    return data