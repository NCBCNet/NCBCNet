from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class Article(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    content = models.TextField()
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ('-created',) # -created倒序排序
    def __str__(self):
        return self.title
