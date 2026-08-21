"""article 序列化器（从 api/serializers/articles.py 迁移，类名与字段保持不变）。

ORM 写入收敛到 article.services（create_article / update_article）。
评论序列化器随评论一起归入文章域（ADR-004）。
"""
import markdown
from rest_framework import serializers

from article.models import Article, ArticleColumn, Comment
from article.services import create_article, update_article
from usermanage.serializers import UserSerializer


class ArticleColumnSerializer(serializers.ModelSerializer):
    """文章栏目序列化器"""
    class Meta:
        model = ArticleColumn
        fields = ['id', 'title', 'created']


class CommentSerializer(serializers.ModelSerializer):
    """评论序列化器（含嵌套子评论）"""
    user = UserSerializer(read_only=True)
    reply_to = UserSerializer(read_only=True)
    children = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'parent', 'reply_to', 'user', 'content', 'created', 'children']
        read_only_fields = ['id', 'created']

    def get_children(self, obj):
        children = obj.children.all()
        if children:
            return CommentSerializer(children, many=True).data
        return []


class ArticleListSerializer(serializers.ModelSerializer):
    """文章列表序列化器（轻量）"""
    author = UserSerializer(read_only=True)
    column = ArticleColumnSerializer(read_only=True)
    tags = serializers.ListField(source='tags.names', read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            'id', 'author', 'title', 'avatar', 'column', 'tags',
            'likes', 'total_views', 'created', 'updated', 'comments_count'
        ]
        read_only_fields = ['id', 'likes', 'total_views', 'created', 'updated']

    def get_comments_count(self, obj):
        return obj.comments.count()


class ArticleDetailSerializer(serializers.ModelSerializer):
    """文章详情序列化器（含完整内容、评论、目录）"""
    author = UserSerializer(read_only=True)
    column = ArticleColumnSerializer(read_only=True)
    tags = serializers.ListField(source='tags.names', read_only=True)
    comments = serializers.SerializerMethodField()
    content_html = serializers.SerializerMethodField()
    toc = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            'id', 'author', 'title', 'avatar', 'column', 'tags',
            'content', 'content_html', 'toc', 'likes', 'total_views',
            'created', 'updated', 'comments'
        ]
        read_only_fields = ['id', 'likes', 'total_views', 'created', 'updated']

    def get_comments(self, obj):
        # 只返回顶级评论（parent=None），子评论通过嵌套序列化展示
        top_comments = Comment.objects.filter(article=obj, parent=None).order_by('created')
        return CommentSerializer(top_comments, many=True).data

    def get_content_html(self, obj):
        md = markdown.Markdown(extensions=[
            'markdown.extensions.extra',
            'markdown.extensions.codehilite',
            'markdown.extensions.toc',
        ])
        return md.convert(obj.content)

    def get_toc(self, obj):
        md = markdown.Markdown(extensions=[
            'markdown.extensions.extra',
            'markdown.extensions.codehilite',
            'markdown.extensions.toc',
        ])
        md.convert(obj.content)
        return md.toc


class ArticleCreateSerializer(serializers.ModelSerializer):
    """创建/编辑文章序列化器"""
    tags = serializers.CharField(required=False, help_text='以逗号分隔的标签')

    class Meta:
        model = Article
        fields = ['title', 'content', 'avatar', 'column', 'tags']

    def create(self, validated_data):
        tags = validated_data.pop('tags', '')
        return create_article(
            author=validated_data.pop('author'),
            title=validated_data['title'],
            content=validated_data['content'],
            column=validated_data.get('column'),
            avatar=validated_data.get('avatar'),
            tags=tags,
        )

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        return update_article(instance, tags=tags, **validated_data)
