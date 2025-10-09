from django.db import models

class Author(models.Model):
    # the id would be created in the serializer by generating a uuid to attach
    # to the end of the host url
    id = models.URLField(primary_key=True) 
    # can use the host to differentiate local and remote users
    # could aslo consider having a bool field for whether a user is local or not
    host = models.URLField() 
    displayName = models.CharField()
    github = models.URLField()
    profileImage = models.URLField()
    web = models.URLField()

    # i saw a this user story:
    # As an author, I want to be able to edit my profile: name, description, picture, and GitHub.
    # so we might need a description field?
    description = models.CharField()