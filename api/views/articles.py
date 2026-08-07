from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from article.models import Article, ArticleColumn
from api.serializers.articles import (
    ArticleListSerializer,
    ArticleDetailSerializer,
    ArticleCreateSerializer,
    ArticleColumnSerializer,
)


class ArticleListView(generics.ListAPIView):
    """文章列表（分页、搜索、排序、栏目/标签筛选）"""
    serializer_class = ArticleListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Article.objects.all()

        # 搜索
        search = self.request.query_params.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(content__icontains=search)
            )

        # 栏目筛选
        column = self.request.query_params.get('column', '')
        if column and column.isdigit():
            queryset = queryset.filter(column_id=column)

        # 标签筛选
        tag = self.request.query_params.get('tag', '')
        if tag and tag != 'None':
            queryset = queryset.filter(tags__name__in=[tag])

        # 排序
        order = self.request.query_params.get('order', '')
        if order == 'total_views':
            queryset = queryset.order_by('-total_views')
        else:
            queryset = queryset.order_by('-created')

        return queryset


class ArticleDetailView(generics.RetrieveAPIView):
    """文章详情"""
    queryset = Article.objects.all()
    serializer_class = ArticleDetailSerializer
    permission_classes = [permissions.AllowAny]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # 增加浏览量
        instance.total_views += 1
        instance.save(update_fields=['total_views'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


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
        return Article.objects.filter(author=self.request.user)


class ArticleDeleteView(generics.DestroyAPIView):
    """删除文章（仅作者）"""
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Article.objects.filter(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({'success': True, 'message': '文章已删除'}, status=status.HTTP_200_OK)


class IncreaseLikesView(APIView):
    """点赞"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            article = Article.objects.get(pk=pk)
            article.likes += 1
            article.save(update_fields=['likes'])
            return Response({'success': True, 'likes': article.likes})
        except Article.DoesNotExist:
            return Response({'error': '文章不存在'}, status=status.HTTP_404_NOT_FOUND)


class ArticleColumnListView(generics.ListAPIView):
    """栏目列表"""
    queryset = ArticleColumn.objects.all()
    serializer_class = ArticleColumnSerializer
    permission_classes = [permissions.AllowAny]
