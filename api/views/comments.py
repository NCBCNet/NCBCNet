import logging

from rest_framework import generics, permissions, status
from rest_framework.response import Response

from article.serializers import CommentSerializer
from article.services import create_comment, reply_comment


logger = logging.getLogger(__name__)


class CommentCreateView(generics.CreateAPIView):
    """发表评论"""
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        try:
            comment = create_comment(
                article_id=kwargs.get('article_id'),
                user=request.user,
                content=request.data.get('content', ''),
            )
        except ValueError:
            logger.exception("Failed to create comment due to invalid input.")
            return Response({'error': 'Invalid request data.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)


class CommentReplyView(generics.CreateAPIView):
    """回复评论"""
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        try:
            comment = reply_comment(
                article_id=kwargs.get('article_id'),
                parent_comment_id=kwargs.get('parent_comment_id'),
                user=request.user,
                content=request.data.get('content', ''),
            )
        except ValueError:
            logger.exception("Failed to reply to comment due to invalid input.")
            return Response({'error': 'Invalid request data.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)
