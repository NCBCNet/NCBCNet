from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from mdeditor.fields import MDTextField
from taggit.managers import TaggableManager
from PIL import Image
from mptt.models import MPTTModel, TreeForeignKey
from django_ckeditor_5.fields import CKEditor5Field

# Create your models here.
class Articletest(models.Model):
    title = models.CharField(max_length=100)
    content = MDTextField()
class ArticleColumn(models.Model):
    """
    栏目的Model
    """
    title = models.CharField(max_length=100,blank=True)
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

class Article(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    avatar = models.ImageField(upload_to='article/%Y%m%d/', blank=True)
    # kinds = {
    #     "at": "article",
    #     "ds": "discussions",
    # }
    # kind = models.CharField(
    #     max_length=2,
    #     choices=kinds,
    #     default="at",
    # )

    def save(self, *args, **kwargs):
        article = super(Article, self).save(*args, **kwargs)
        if self.avatar and not kwargs.get('update_fields'):
            # Pillow 10+ 已移除 Image.ANTIALIAS，改用 Image.Resampling.LANCZOS
            try:
                with Image.open(self.avatar.path) as img:
                    (x, y) = img.size
                    new_x = 400
                    new_y = int(new_x * y / x) if x else 400
                    resized = img.resize((new_x, new_y), Image.Resampling.LANCZOS)
                resized.save(self.avatar.path)
            except Exception:
                # 缩略失败（损坏图片/非本地存储）不阻断保存
                pass
        return article
    column = models.ForeignKey(ArticleColumn,null=True,blank=True,on_delete=models.CASCADE,related_name='article')
    tags = TaggableManager(blank=True)
    likes = models.PositiveIntegerField(default=0)
    content = MDTextField()
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)
    total_views = models.PositiveIntegerField(default=0)
    class Meta:
        ordering = ('-created',) # -created倒序排序
    def __str__(self):
        return self.title
    def get_absolute_url(self):
        return reverse('article:article_detail',args=[self.id])

class Comment(MPTTModel):
    """评论（ADR-004：从 comment 应用并入文章域）。

    db_table 保留为 comment_comment，物理表在既有安装中已存在，
    迁移 0006 使用 SeparateDatabaseAndState 只登记状态、不重复建表。
    """
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    reply_to = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='replyers')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = CKEditor5Field(config_name='extends')
    created = models.DateTimeField(auto_now_add=True)

    class MPTTMeta:
        order_insertion_by = ['created']

    class Meta:
        db_table = 'comment_comment'

    def __str__(self):
        return self.content[:20]

