from django.db import models

class Entry(models.Model):
    title = models.CharField()
    id = models.URLField(primary_key=True)
    web = models.URLField()
    description = models.CharField() # or possible a textfield
    class ContentType(models.TextChoices):
        MARKDOWN = "text/markdown",
        PLAIN = "text/plain",
        NOTJPEGORPNG = "application/base64",
        PNG = "image/png;base64",
        JPEG = "image/jpeg;base64"
    contentType = models.CharField(choices=ContentType)
    content = models.TextField()
    author = models.ForeignKey(Author)
    # ManyToManyField:
    # https://docs.djangoproject.com/en/5.2/ref/models/fields/#field-types
    # https://stackoverflow.com/questions/67623667/django-models-to-hold-a-list-of-objects-from-another-model
    comments = models.ManyToManyField(Comment)
    likes = models.ManyToManyField(Like)
    published = models.DateTimeField()
    # TextChoices : https://docs.djangoproject.com/en/5.2/ref/models/fields/#field-types
    class Visibility(models.TextChoices):
        PUBLIC = "PUBLIC",
        FRIENDS = "FRIENDS",
        UNLISTED = "UNLISTED",
        DELETED = "DELETED"
    visibility = models.CharField(choices=Visibility)

class Like(models.Model):
    author = models.ForeignKey(Author)
    # https://docs.djangoproject.com/en/5.2/ref/utils/#django.utils.timezone.now
    # https://stackoverflow.com/questions/26063681/django-model-datetimefield-from-an-iso8601-timestamp-string
    # the serializer for the Likes model should handle parsing the datetimefield
    published = models.DateTimeField()
    id = models.URLField(primary_key=True)
    object_liked = models.URLField()

class Comment(models.Model):
    author = models.ForeignKey(Author)
    comment = models.CharField()
    # will content type for comments always be markdown?
    # or should I change it to be choices like content type in the Entry class
    contentType = models.CharField()
    published = models.DateTimeField() 
    id = models.URLField(primary_key=True)
    entry = models.URLField()
    likes = models.ManyToManyField(Like)
    # the web field is in the Comments object in the Project descrtiption so i added it here
    web = models.URLField() # keep if we decide we will have an html page with the ability to only view one comment at a time