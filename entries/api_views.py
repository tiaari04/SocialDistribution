from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from .models import Entry, Comment, Like
from .serializers import CommentSerializer, LikeSerializer
from .permissions import can_access_entry
from django.db import transaction
from django.utils import timezone
from .utils import resolve_author_from_request
from authors.models import Author


class SmallPage(PageNumberPagination):
    page_size = 5


class EntryCommentsViewSet(viewsets.ViewSet):
    pagination_class = SmallPage
    permission_classes = [AllowAny]

    def _resolve_entry(self, author_serial=None, entry_serial=None, entry_fqid=None):
        if entry_fqid:
            return get_object_or_404(Entry, fqid=entry_fqid)
        return get_object_or_404(Entry, serial=entry_serial, author__serial=author_serial)

    def list(self, request, author_serial=None, entry_serial=None, entry_fqid=None):
        entry = self._resolve_entry(author_serial, entry_serial, entry_fqid)
        req_author = resolve_author_from_request(request)

        if not can_access_entry(req_author, entry):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        qs = entry.comments.all().order_by('published', 'created')
        paginator = SmallPage()
        page = paginator.paginate_queryset(qs, request)
        serializer = CommentSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def create(self, request, author_serial=None, entry_serial=None, entry_fqid=None):
        entry = self._resolve_entry(author_serial, entry_serial, entry_fqid)
        req_author = resolve_author_from_request(request)

        if not can_access_entry(req_author, entry):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        content = data.get('content') or data.get('comment')
        content_type = data.get('content_type') or data.get('contentType') or Entry.ContentType.MARKDOWN

        fqid = data.get('id')
        published = data.get('published') or timezone.now()

        comment = Comment.objects.create(
            fqid=fqid or f"{entry.fqid}#comment-{timezone.now().timestamp()}",
            author=req_author,
            entry=entry,
            content=content or '',
            content_type=content_type,
            published=published,
            web=data.get('web', ''),
        )
        serializer = CommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EntryLikesViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    def _resolve_entry(self, author_serial=None, entry_serial=None, entry_fqid=None):
        if entry_fqid:
            return get_object_or_404(Entry, fqid=entry_fqid)
        return get_object_or_404(Entry, serial=entry_serial, author__serial=author_serial)

    def list(self, request, author_serial=None, entry_serial=None, entry_fqid=None):
        entry = self._resolve_entry(author_serial, entry_serial, entry_fqid)
        req_author = None
        req_author = resolve_author_from_request(request)

        if not can_access_entry(req_author, entry):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        qs = Like.objects.filter(object_fqid=entry.fqid).order_by('-published', '-created')
        page_size = int(request.query_params.get('size', 50))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        items = qs[start:end]
        serializer = LikeSerializer(items, many=True)
        return Response({'type': 'likes', 'count': qs.count(), 'src': serializer.data})

    @transaction.atomic
    def create(self, request, author_serial=None, entry_serial=None, entry_fqid=None):
        entry = self._resolve_entry(author_serial, entry_serial, entry_fqid)
        req_author = resolve_author_from_request(request)

        if not can_access_entry(req_author, entry):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        if req_author:
            existing = Like.objects.filter(author=req_author, object_fqid=entry.fqid).first()
            if existing:
                serializer = LikeSerializer(existing)
                return Response(serializer.data, status=status.HTTP_200_OK)

        liked_fqid = request.data.get('id') or f"{entry.fqid}#like-{timezone.now().timestamp()}"
        like = Like.objects.create(fqid=liked_fqid, author=req_author, object_fqid=entry.fqid, published=timezone.now())
        serializer = LikeSerializer(like)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CommentLikesViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    def _resolve_comment(self, author_serial=None, entry_serial=None, entry_fqid=None, comment_fqid=None):
        return get_object_or_404(Comment, fqid=comment_fqid)

    def list(self, request, author_serial=None, entry_serial=None, entry_fqid=None, comment_fqid=None):
        comment = self._resolve_comment(author_serial, entry_serial, entry_fqid, comment_fqid)
        # determine requesting author
        req_author = None
        req_author = resolve_author_from_request(request)

        # check access to parent entry
        if not can_access_entry(req_author, comment.entry):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        qs = Like.objects.filter(object_fqid=comment.fqid).order_by('-published', '-created')
        page_size = int(request.query_params.get('size', 50))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        items = qs[start:end]
        serializer = LikeSerializer(items, many=True)
        return Response({'type': 'likes', 'count': qs.count(), 'src': serializer.data})

    @transaction.atomic
    def create(self, request, author_serial=None, entry_serial=None, entry_fqid=None, comment_fqid=None):
        comment = self._resolve_comment(author_serial, entry_serial, entry_fqid, comment_fqid)
        req_author = resolve_author_from_request(request)

        if not can_access_entry(req_author, comment.entry):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        if req_author:
            existing = Like.objects.filter(author=req_author, object_fqid=comment.fqid).first()
            if existing:
                serializer = LikeSerializer(existing)
                return Response(serializer.data, status=status.HTTP_200_OK)

        liked_fqid = request.data.get('id') or f"{comment.fqid}#like-{timezone.now().timestamp()}"
        like = Like.objects.create(fqid=liked_fqid, author=req_author, object_fqid=comment.fqid, published=timezone.now())
        serializer = LikeSerializer(like)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
