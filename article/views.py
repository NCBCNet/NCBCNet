from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views import View

from .models import Article, ArticleColumn
import markdown
from django.shortcuts import redirect
from django.http import HttpResponse
from .forms import ArticlePostForm
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from comment.models import Comment
from comment.forms import CommentForm

# Create your views here.

def article_list(request):
    search = request.GET.get('search')
    order = request.GET.get('order')
    column = request.GET.get('column')
    tag = request.GET.get('tag')

    article_list = Article.objects.all()

    if search:
        article_list = article_list.filter(
            Q(title__icontains=search) |
            Q(body__icontains=search)
        )
    else:
        search = ''

        # 栏目查询集
    if column is not None and column.isdigit():
        article_list = article_list.filter(column=column)

        # 标签查询集
    if tag and tag != 'None':
        article_list = article_list.filter(tags__name__in=[tag])

        # 查询集排序
    if order == 'total_views':
        article_list = article_list.order_by('-total_views')

    paginator = Paginator(article_list, 10)
    page = request.GET.get('page')
    articles = paginator.get_page(page)

    context = {"articles":articles,'order':order,'search':search}
    return render(request, 'article/list.html', context)


def article_detail(request, id):
    article = Article.objects.get(id=id)
    comments = Comment.objects.filter(article=id)
    article.total_views += 1
    article.save(update_fields=['total_views'])
    comment_form = CommentForm()
    md = markdown.Markdown(extensions=[
                                            'markdown.extensions.extra',
                                            'markdown.extensions.codehilite',
                                            'markdown.extensions.toc',
                                        ]
                                        )
    article.content = md.convert(article.content)
    context = {'article': article,'toc':md.toc,'comments':comments,'comment_form':comment_form,}
    return render(request, 'article/detail.html', context)


@login_required(login_url='usermanage:login')
def article_create(request):
    if request.method == 'POST':
        form = ArticlePostForm(request.POST,request.FILES)
        if form.is_valid():
            new_article = form.save(commit=False)
            new_article.author = User.objects.get(id=request.user.id)
            if request.POST['column'] != 'none':
                new_article.column = ArticleColumn.objects.get(id=request.POST['column'])
            new_article.save()
            form.save_m2m()
            return redirect('article:list')
        else:
            return HttpResponse(form.errors, status=400)
    else:
        article_form = ArticlePostForm()
        columns = ArticleColumn.objects.all()
        context = {'article_form': article_form,'columns':columns}
        return render(request, 'article/create_article.html', context)


@login_required(login_url='usermanage:login')
def article_update(request, id):
    article = Article.objects.get(id=id)
    if request.user == article.author:
        if request.method == 'POST':
            form = ArticlePostForm(data=request.POST)
            if form.is_valid():
                article.title = request.POST['title']
                article.content = request.POST['content']
                if request.POST['column'] != 'none':
                    article.column = ArticleColumn.objects.get(id=request.POST['column'])
                else:
                    article.column = None
                if request.POST['tags'] != '':
                    pass
                else:
                    pass
                article.save()
                return redirect('article:article_detail', id=id)
            else:
                return HttpResponse("表单有误")
        else:
            article_form = ArticlePostForm()
            columns = ArticleColumn.objects.all()
            tagson = ''
            for tag in article.tags.all():
                tagson += tag.name + ','
            tagson = tagson[:-1]
            context = {'article_form': article_form, 'article': article,'columns':columns,"tags":tagson}
            return render(request, 'article/updata_article.html', context)
    else:
        return HttpResponse("你没有权限")


@login_required(login_url='usermanage:login')
def article_delete(request, id):
    article = Article.objects.get(id=id)
    if request.user == article.author:
        if request.method == 'POST':
            article.delete()
            return redirect('article:list')
        else:
            return HttpResponse('仅允许POST请求')
    else:
        return HttpResponse("你没有权限")


class IncreaseLikesView(View):
    def post(self, request, *args, **kwargs):
        article = Article.objects.get(id=kwargs.get('id'))
        article.likes +=1
        article.save()
        return HttpResponse('success')