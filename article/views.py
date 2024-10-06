from django.shortcuts import render
from django.template.context_processors import request

from .models import Article
import markdown
from django.shortcuts import redirect
from django.http import HttpResponse
from .forms import ArticlePostForm
from django.contrib.auth.models import User
# Create your views here.

def article_list(request):
    articles = Article.objects.all()
    context = {'articles':articles}
    return render(request, 'article/list.html',context)

def article_detail(request,id):
    article = Article.objects.get(id=id)
    article.content = markdown.markdown(article.content,
                                extensions=[
                                    'markdown.extensions.extra',
                                    'markdown.extensions.codehilite',
                                ]
                                )
    context = {'article':article}
    return render(request,'article/detail.html',context)

def article_create(request):
    if request.method == 'POST':
        form = ArticlePostForm(data=request.POST)
        if form.is_valid():
            new_article = form.save(commit=False)
            new_article.author = User.objects.get(id=1)
            new_article.save()
            return redirect('article:list')
        else:
            return HttpResponse(form.errors, status=400)
    else:
        article_form = ArticlePostForm()
        context = {'article_form':article_form}
        return render(request,'article/create_article.html',context)

def article_update(request,id):
    article = Article.objects.get(id=id)
    if request.method == 'POST':
        form = ArticlePostForm(data=request.POST)
        if form.is_valid():
            article.title = request.POST['title']
            article.content = request.POST['content']
            article.save()
            return redirect('article:article_detail',id=id)
        else:
            return HttpResponse("表单有误")
    else:
        article_form = ArticlePostForm()
        context = {'article_form':article_form,'article':article}
        return render(request,'article/updata_article.html',context)

def article_delete(request,id):
    if request.method == 'POST':
        article = Article.objects.get(id=id)
        article.delete()
        return redirect('article:list')
    else:
        return HttpResponse('仅允许POST请求')