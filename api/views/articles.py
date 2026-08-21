from django.http import Http404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from article.serializers import (
    ArticleListSerializer,
    ArticleDetailSerializer,
    ArticleCreateSerializer,
    ArticleColumnSerializer,
)
from article.services import (
    delete_article,
    get_article,
    increase_likes,
    list_articles,
    list_columns,
)


class ArticleListView(generics.ListAPIView):
    """文章列表（分页、搜索、排序、栏目/标签筛选）"""
    serializer_class = ArticleListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return list_articles(
            search=self.request.query_params.get('search', ''),
            column=self.request.query_params.get('column', ''),
            tag=self.request.query_params.get('tag', ''),
            order=self.request.query_params.get('order', ''),
        )


class ArticleDetailView(generics.RetrieveAPIView):
    """文章详情（阅读时增加浏览量）"""
    serializer_class = ArticleDetailSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        return get_article(self.kwargs['pk'], increase_views=True)


class ArticleCreateView(generics.CreateAPIView):
    """创建文章"""
    serializer_class = ArticleCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class ArticleUpdateView(generics.UpdateAPIView):
    """更新文章（仅作者）"""
    serializer_class = ArticleCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return list_articles().filter(author=self.request.user)


class ArticleDeleteView(generics.DestroyAPIView):
    """删除文章（仅作者）"""
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return list_articles().filter(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        delete_article(instance)
        return Response({'success': True, 'message': '文章已删除'}, status=status.HTTP_200_OK)


class IncreaseLikesView(APIView):
    """点赞"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            article = increase_likes(pk)
            return Response({'success': True, 'likes': article.likes})
        except Http404:
            return Response({'error': '文章不存在'}, status=status.HTTP_404_NOT_FOUND)


class ArticleColumnListView(generics.ListAPIView):
    """栏目列表"""
    queryset = list_columns()
    serializer_class = ArticleColumnSerializer
    permission_classes = [permissions.AllowAny]
