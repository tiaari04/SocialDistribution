from rest_framework import serializers
from authors.models import Author
from .models import Comment, Like, Entry


class AuthorRefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'displayName', 'host', 'web', 'profileImage']


class CommentSerializer(serializers.ModelSerializer):
    author = AuthorRefSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['fqid', 'author', 'content', 'content_type', 'published', 'web', 'entry', 'likes_count']
        read_only_fields = ['fqid', 'author', 'published', 'likes_count']


class LikeSerializer(serializers.ModelSerializer):
    author = AuthorRefSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ['fqid', 'author', 'object_fqid', 'published']
        read_only_fields = ['fqid', 'author', 'published']
