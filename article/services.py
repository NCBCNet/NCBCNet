"""article 业务服务层（阶段二 M2：模块化单体，ADR-004 评论并入文章域）。

约定：所有 ORM 操作与事务边界（transaction.atomic）都收敛在本层，
api 视图只做请求解析 / 序列化 / 响应组装，不再直接触碰模型。
评论（Comment）已从 comment 应用并入 article 域，相关服务函数一并收敛于此。
"""
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404

from article.models import Article, ArticleColumn, Comment


# ---------------------------------------------------------------------------
# 文章
# ---------------------------------------------------------------------------
def list_articles(search='', column=None, tag=None, order=''):
    """文章列表：搜索 / 栏目 / 标签筛选 + 排序。"""
    queryset = Article.objects.all()

    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) |
            Q(content__icontains=search)
        )

    if column and str(column).isdigit():
        queryset = queryset.filter(column_id=column)

    if tag and tag != 'None':
        queryset = queryset.filter(tags__name__in=[tag])

    if order == 'total_views':
        queryset = queryset.order_by('-total_views')
    else:
        queryset = queryset.order_by('-created')

    return queryset


def get_article(pk, increase_views=False):
    """获取文章（不存在则 404）；increase_views=True 时阅读量 +1。"""
    article = get_object_or_404(Article, pk=pk)
    if increase_views:
        with transaction.atomic():
            article.total_views += 1
            article.save(update_fields=['total_views'])
    return article


def _apply_tags(article, tags_str):
    """解析逗号分隔标签并挂到文章上（仅在非空时执行）。"""
    tag_names = [t.strip() for t in tags_str.split(',') if t.strip()]
    if tag_names:
        article.tags.add(*tag_names)


def create_article(author, title, content, column=None, avatar=None, tags=''):
    """创建文章（事务内）。"""
    with transaction.atomic():
        article = Article.objects.create(
            author=author,
            title=title,
            content=content,
            column=column,
            avatar=avatar,
        )
        if tags:
            _apply_tags(article, tags)
        return article


def update_article(article, tags=None, **fields):
    """更新文章（事务内）。

    fields 为待写字段；tags 语义与原序列化器一致：
    None 表示不修改标签，'' 表示清空标签，非空字符串表示清空后重挂。
    """
    with transaction.atomic():
        for attr, value in fields.items():
            setattr(article, attr, value)
        article.save()
        if tags is not None:
            article.tags.clear()
            if tags:
                _apply_tags(article, tags)
        return article


def delete_article(article):
    """删除文章（事务内，评论随 article FK CASCADE 一并删除）。"""
    with transaction.atomic():
        article.delete()


def increase_likes(pk):
    """点赞：likes +1（事务内）；文章不存在抛 Http404。"""
    try:
        article = Article.objects.get(pk=pk)
    except Article.DoesNotExist:
        raise Http404('文章不存在')
    with transaction.atomic():
        article.likes += 1
        article.save(update_fields=['likes'])
        return article


def list_columns():
    """栏目列表。"""
    return ArticleColumn.objects.all()


# ---------------------------------------------------------------------------
# 评论（评论归属文章域，ADR-004）
# ---------------------------------------------------------------------------
def create_comment(article_id, user, content):
    """发表评论：文章不存在抛 Http404；内容为空抛 ValueError。"""
    article = get_object_or_404(Article, id=article_id)
    if not content:
        raise ValueError('评论内容不能为空')
    with transaction.atomic():
        return Comment.objects.create(
            article=article,
            user=user,
            content=content,
        )


def reply_comment(article_id, parent_comment_id, user, content):
    """回复评论：父评论挂在根节点下并记录 reply_to；文章/父评论不存在抛 Http404。"""
    article = get_object_or_404(Article, id=article_id)
    parent_comment = get_object_or_404(Comment, id=parent_comment_id)
    if not content:
        raise ValueError('回复内容不能为空')
    with transaction.atomic():
        return Comment.objects.create(
            article=article,
            user=user,
            content=content,
            parent_id=parent_comment.get_root().id,
            reply_to=parent_comment.user,
        )
