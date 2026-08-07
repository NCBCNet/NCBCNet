from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from comment.models import Comment
from article.models import Article
from api.serializers.articles import CommentSerializer


class CommentCreateView(generics.CreateAPIView):
    """发表评论"""
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        article_id = kwargs.get('article_id')
        article = get_object_or_404(Article, id=article_id)

        content = request.data.get('content', '')
        if not content:
            return Response({'error': '评论内容不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        comment = Comment.objects.create(
            article=article,
            user=request.user,
            content=content,
        )
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)


class CommentReplyView(generics.CreateAPIView):
    """回复评论"""
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        article_id = kwargs.get('article_id')
        parent_comment_id = kwargs.get('parent_comment_id')

        article = get_object_or_404(Article, id=article_id)
        parent_comment = get_object_or_404(Comment, id=parent_comment_id)

        content = request.data.get('content', '')
        if not content:
            return Response({'error': '回复内容不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        comment = Comment.objects.create(
            article=article,
            user=request.user,
            content=content,
            parent_id=parent_comment.get_root().id,
            reply_to=parent_comment.user,
        )
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)
