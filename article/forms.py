from django import forms
from .models import Article

class ArticlePostForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'content','tags']