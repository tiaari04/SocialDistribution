from django.core import serializers
from authors.models import Author
from inbox.models import FollowRequest

def serialize_followers_view(author, typ):
    followers = []
    resp_type = ''

    if typ == 1:
        followers = FollowRequest.objects.filter(author_followed=author, state=FollowRequest.State.ACCEPTED).select_related('actor')
        resp_type = 'followers'

    if typ == 2:
        followers = FollowRequest.objects.filter(author_followed=author, state=FollowRequest.State.REQUESTING).select_related('actor')
        resp_type = 'follow requests'

    data = []
    for follow_request in followers:
        actor_data = follow_request.actor
        data.append({
            'type': 'author',
            'id': actor_data.id,
            'host': actor_data.host,
            'displayName': actor_data.displayName,
            'web': actor_data.web,
            'github': actor_data.github,
            'profileImage': actor_data.profileImage
        })

    resp = {'type':resp_type, 'followers':data}
    return resp, 200