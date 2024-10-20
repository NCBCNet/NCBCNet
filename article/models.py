from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from taggit.managers import TaggableManager
from PIL import Image
# Create your models here.

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

    def save(self,*args ,**kwargs):
        article = super(Article,self).save(*args,**kwargs)
        if self.avatar and not kwargs.get('update_fields'):
            image = Image.open(self.avatar)
            (x,y) = image.size
            new_x = 400
            new_y = int(new_x*y/x)
            resized_image = image.resize((new_x,new_y),Image.ANTIALIAS) # Pillow新版无法使用
            resized_image.save(self.avatar.path)
        return article
    column = models.ForeignKey(ArticleColumn,null=True,blank=True,on_delete=models.CASCADE,related_name='article')
    tags = TaggableManager(blank=True)
    likes = models.PositiveIntegerField(default=0)
    content = models.TextField()
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)
    total_views = models.PositiveIntegerField(default=0)
    class Meta:
        ordering = ('-created',) # -created倒序排序
    def __str__(self):
        return self.title
    def get_absolute_url(self):
        return reverse('article:article_detail',args=[self.id])

