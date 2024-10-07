from lib2to3.fixes.fix_input import context

from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from .forms import UserLoginForm,UserRegisterForm,ProfileForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Profile
# Create your views here.

def user_register(request):
    if request.method == 'POST':
        form = UserRegisterForm(data=request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.set_password(form.cleaned_data['password'])
            new_user.save()
            login(request, new_user)
            return redirect('server:index')
        else:
            return HttpResponse("输入有误")
    elif request.method == 'GET':
        form = UserRegisterForm()
        context = {'form': form}
        return render(request,'usermanage/register.html',context)
    else:
        return HttpResponse("仅允许GET或POST")
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

@login_required(login_url='usermanage:login')
def user_delete(request,id):
    if request.method == 'POST':
        user = User.objects.get(id=id)
        if request.user == user:
            logout(request)
            user.delete()
            return redirect('server:index')
        else:
            return HttpResponse("你没有删除权限")
    else:
        return HttpResponse("仅允许POST请求")

@login_required(login_url='usermanage:login')
def edit_profile(request,id):
    user = User.objects.get(id=id)
    # user_id 是 OneToOneField 自动生成的字段
    # profile = Profile.objects.get(user_id=id)
    if Profile.objects.filter(user_id=id).exists():
        profile = Profile.objects.get(user_id=id)
    else:
        profile = Profile.objects.create(user=user)
    if request.method == 'POST':
        if request.user != user:
            return HttpResponse("你没有权限")
        profile_form = ProfileForm(request.POST,request.FILES)
        if profile_form.is_valid():
            profile_cd = profile_form.cleaned_data
            profile.phone = profile_cd['phone']
            profile.bio = profile_cd['bio']
            if 'avatar' in request.FILES:
                profile.avatar = profile_cd['avatar']
            profile.save()
            return redirect('usermanage:edit_profile',id=id)
        else:
            return HttpResponse("注册表单输入有误。请重新输入~")
    elif request.method == 'GET':
        profile_form = ProfileForm()
        context = {'profile_form': profile_form,'user':user,'profile':profile}
        return render(request,'usermanage/profile.html',context)
    else:
        return HttpResponse("请使用GET或POST请求数据")