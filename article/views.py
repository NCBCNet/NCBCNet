from django.shortcuts import render
from .models import Article
# Create your views here.

def article_list(request):
    articles = Article.objects.all()
    context = {'articles':articles}
    return render(request, 'article/list.html',context)