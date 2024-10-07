from django import forms
from django.contrib.auth.models import User

from .models import Profile


class UserLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField()

class UserRegisterForm(forms.ModelForm):
    password = forms.CharField()
    password2 = forms.CharField()
    class Meta:
        model = User
        fields = {'username','email'}

    def clean_password2(self):
        data = self.cleaned_data
        if data.get('password') == data.get('password2'):
            return data.get('password')
        else:
            return forms.ValidationError('密码不一致！')

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = {'phone','avatar','bio'}