from django.db import models
from authors.models import Author

class FollowRequest(models.Model):
    # by querying this table we should be able to tell who is being followed by who, who rejected/accepted
    # or has pending requests, and which users are friends whether or not they are from different nodes
    id = models.AutoField(primary_key=True)

    # the author requesting to follow
    actor = models.ForeignKey(Author)
    # the author recieving the request
    # might need to change the name back to object
    author_followed = models.ForeignKey(Author)

    # if a local user sends a request to another local user we store it as any of the choices
    # based on what the recieving local user decides.
    # if a local user sends a request to a remote user we store it as accepted since we won't
    # recieve a response back
    # if a local user recieves a request from a remote user it is stored as whatever choice they made
    class State(models.TextChoices):
        REQ = "requesting",
        ACC = "accepted",
        REJ = "rejected"
    state = models.CharField(choices=State)

    # i asssume we would want to be able to order a user's follow requests somehow?
    published = models.DateTimeField()

    # so requests can't be sent to the same people multiple times
    class Meta:
        unique_together = ('actor', 'author_followed')