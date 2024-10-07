from django.contrib import admin
from .models import Article,ArticleColumn
# Register your models here.
admin.site.register(Article)
admin.site.register(ArticleColumn)