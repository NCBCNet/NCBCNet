from django import forms
from .models import Article, Comment

class ArticlePostForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'content','tags','avatar']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
