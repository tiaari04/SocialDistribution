from django.core import serializers
from authors.models import Author
from inbox.models import FollowRequest

def serialize_followers_view(author):
    followers = FollowRequest.objects.filter(author_followed=author, state=FollowRequest.State.ACCEPTED).select_related('actor')

    if not followers:
        return {'type':'followers', 'followers':[]}, 204

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

    resp = {'type':'followers', 'followers':data}
    return resp, 200