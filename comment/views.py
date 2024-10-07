from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from article.models import Article
from .forms import CommentForm

@login_required(login_url='usermanage:login')
def post_comment(request,article_id):
    article = get_object_or_404(Article, id=article_id)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.article = article
            comment.user = request.user
            comment.save()
            return redirect(article)
        else:
            return HttpResponse("表单内容有误，请重新填写。")
    else:
        return HttpResponse("发表评论仅接受POST请求。")
