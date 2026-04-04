from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views import View

from .models import Article, ArticleColumn
import markdown
from django.shortcuts import redirect
from django.http import HttpResponse, JsonResponse
from .forms import ArticlePostForm
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from comment.models import Comment
from comment.forms import CommentForm
from rest_framework.decorators import api_view
from rest_framework.response import Response

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
            form.content = request.POST['content']
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
            article_form = ArticlePostForm(initial={'content':article.content})
            columns = ArticleColumn.objects.all()
            tagson = ''
            for tag in article.tags.all():
                tagson += tag.name + ','
            tagson = tagson[:-1]
            context = {'article_form': article_form, 'article': article,'columns':columns,"tags":tagson}
            return render(request, 'article/updata_article.html', context)
    else:
        return redirect('server:illegal_request')


@login_required(login_url='usermanage:login')
def article_delete(request, id):
    article = Article.objects.get(id=id)
    if request.user == article.author:
        if request.method == 'POST':
            article.delete()
            return redirect('article:list')
        else:
            return redirect('server:illegal_request')
    else:
        return redirect('server:illegal_request')


class IncreaseLikesView(View):
    def post(self, request, *args, **kwargs):
        article = Article.objects.get(id=kwargs.get('id'))
        article.likes +=1
        article.save()
        return HttpResponse('success')


# ========== JSON API Views for React Frontend ==========

@api_view(['GET'])
def article_list_api(request):
    search = request.GET.get('search', '')
    order = request.GET.get('order', '')
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))

    articles_qs = Article.objects.all()
    if search:
        articles_qs = articles_qs.filter(
            Q(title__icontains=search) | Q(content__icontains=search)
        )
    if order == 'total_views':
        articles_qs = articles_qs.order_by('-total_views')

    paginator = Paginator(articles_qs, page_size)
    page_obj = paginator.get_page(page)

    data = {
        'count': paginator.count,
        'num_pages': paginator.num_pages,
        'current_page': page,
        'results': [
            {
                'id': a.id,
                'title': a.title,
                'content_preview': a.content[:200] if a.content else '',
                'created': a.created.isoformat(),
                'author': a.author.username,
                'likes': a.likes,
                'total_views': a.total_views,
            }
            for a in page_obj
        ]
    }
    return Response(data)


@api_view(['GET'])
def article_detail_api(request, id):
    try:
        article = Article.objects.get(id=id)
    except Article.DoesNotExist:
        return Response({'error': '文章不存在'}, status=404)

    article.total_views += 1
    article.save(update_fields=['total_views'])

    md = markdown.Markdown(extensions=[
        'markdown.extensions.extra',
        'markdown.extensions.codehilite',
        'markdown.extensions.toc',
    ])
    content_html = md.convert(article.content)

    tags = [tag.name for tag in article.tags.all()]
    data = {
        'id': article.id,
        'title': article.title,
        'content': content_html,
        'toc': md.toc,
        'created': article.created.isoformat(),
        'updated': article.updated.isoformat(),
        'author': article.author.username,
        'author_id': article.author.id,
        'likes': article.likes,
        'total_views': article.total_views,
        'tags': tags,
        'column': article.column.title if article.column else None,
    }
    return Response(data)


@api_view(['POST'])
def article_create_api(request):
    if not request.user.is_authenticated:
        return Response({'error': '请先登录'}, status=401)

    title = request.data.get('title', '').strip()
    content = request.data.get('content', '').strip()

    if not title:
        return Response({'error': '标题不能为空'}, status=400)
    if not content:
        return Response({'error': '内容不能为空'}, status=400)

    article = Article.objects.create(
        author=request.user,
        title=title,
        content=content,
    )
    return Response({'id': article.id, 'success': True}, status=201)


@api_view(['POST'])
def article_like_api(request, id):
    try:
        article = Article.objects.get(id=id)
    except Article.DoesNotExist:
        return Response({'error': '文章不存在'}, status=404)

    article.likes += 1
    article.save(update_fields=['likes'])
    return Response({'likes': article.likes})