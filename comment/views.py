from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse


from article.models import Article
from .forms import CommentForm
from .models import Comment

@login_required(login_url='usermanage:login')
def post_comment(request,article_id,parent_comment_id=None):
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
        return HttpResponse("发表评论仅接受GET/POST请求。")
