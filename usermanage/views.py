from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from .forms import UserLoginForm

# Create your views here.

def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = authenticate(username=data['username'], password=data['password'])
            if user:
                login(request, user)
                return redirect('server:index')
            else:
                return HttpResponse("账号或密码有误")
        else:
            return HttpResponse("输入不合法")
    elif request.method == 'GET':
        form = UserLoginForm()
        context = {'form': form}
        return render(request,'usermanage/login.html',context)
    else:
        return HttpResponse("不是GET或POST请求")

def user_logout(request):
    logout(request)
    return redirect('server:index')