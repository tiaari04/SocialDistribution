from rest_framework import serializers
from authors.models import Author
from .models import Comment, Like, Entry


class AuthorRefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'displayName', 'host', 'web', 'profileImage']


class CommentSerializer(serializers.ModelSerializer):
    user_liked = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'fqid', 'author', 'content', 'content_type', 
            'published', 'likes_count', 'web', 'user_liked'
        ]

    def get_user_liked(self, obj):
        """
        Returns True if the requesting user has liked this comment.
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        try:
            author = Author.objects.get(user=request.user)
        except Author.DoesNotExist:
            return False

        return Like.objects.filter(author=author, object_fqid=obj.fqid).exists()

class LikeSerializer(serializers.ModelSerializer):
    author = AuthorRefSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ['fqid', 'author', 'object_fqid', 'published']
        read_only_fields = ['fqid', 'author', 'published']


class EntrySerializer(serializers.ModelSerializer):
    author = AuthorRefSerializer(read_only=True)

    class Meta:
        model = Entry
        fields = [
            'fqid', 'serial', 'title', 'web', 'description', 'content',
            'image_url', 'content_type', 'author', 'published', 'is_edited',
            'likes_count', 'visibility'
        ]
        read_only_fields = ['fqid', 'author', 'published', 'likes_count']
