from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views import View

from .models import Article, ArticleColumn, Comment
import markdown
from django.shortcuts import redirect
from django.http import HttpResponse
from .forms import ArticlePostForm, CommentForm
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q

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


@login_required(login_url='usermanage:login')
def post_comment(request,article_id,parent_comment_id=None):
    """旧 MVT 评论发表/回复（阶段一冻结链路；评论已并入 article 域）。

    原 comment 应用删除后，本视图承接 /comment/ 前缀下的兼容路由
    （见 article/comment_urls.py，namespace 仍为 comment）。
    """
    article = get_object_or_404(Article, id=article_id)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.article = article
            comment.user = request.user
            if parent_comment_id:
                parent_comment = Comment.objects.get(id=parent_comment_id)
                comment.parent_id = parent_comment.get_root().id
                comment.reply_to = parent_comment.user
                comment.save()
                return HttpResponse('200 OK')
            comment.save()
            return redirect(article)
        else:
            return HttpResponse("表单内容有误，请重新填写。")
    elif request.method == "GET":
        comment_form = CommentForm()
        context = {
            'comment_form': comment_form,
            'article_id':article_id,
            'parent_comment_id':parent_comment_id,
        }
        return render(request,'comment/reply.html',context)
    else:
        return redirect('server:illegal_request')