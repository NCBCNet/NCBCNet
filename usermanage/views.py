from tokenize import group

from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login, logout,alogin
from django.http import HttpResponse,JsonResponse
from django.urls import reverse
from asgiref.sync import sync_to_async
from .forms import UserLoginForm,UserRegisterForm,ProfileForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Profile
# from django.views.decorators.http import require_http_methods
# Create your views here.

# 注意：限流已统一迁移到 DRF throttle（api/throttles.py），
# 旧模板登录/注册由 SPA 的 /api/v1/auth/* 端点（带限流）取代。
async def user_register(request):
    if request.method == 'POST':
        form = UserRegisterForm(data=request.POST)
        is_valid = await sync_to_async(form.is_valid)()
        JsonErr = {'success': False, 'errors':{}}
        if is_valid:
            if form.cleaned_data.get('password') == form.cleaned_data.get('password2'):
                new_user = await sync_to_async(form.save)(commit=False)
                await sync_to_async(new_user.set_password)(form.cleaned_data['password'])
                await sync_to_async(new_user.save)()
                await alogin(request, new_user)
                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('server:index')
                })
            else:
                JsonErr['errors']['password2'] = [{'message': '两次输入的密码不一致，请重新输入', 'code': 'password_mismatch'}]
                return JsonResponse(JsonErr,status=400)
        else:
            JsonErr['errors'] = form.errors.get_json_data()
            return JsonResponse(JsonErr,status=400)
    elif request.method == 'GET':
        form = UserRegisterForm()
        context = {'form': form}
        return render(request,'usermanage/register.html',context)
    else:
        return HttpResponse("仅允许GET或POST")

async def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = await sync_to_async(authenticate)(username=data['username'], password=data['password'])
            if user:
                await alogin(request, user)
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'redirect_url': reverse('server:index')})
                return redirect('server:index')
            else:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': '账号或密码有误，请重新输入'})
                return HttpResponse("账号或密码有误")
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': '输入不合法'})
            return HttpResponse("输入不合法")
    elif request.method == 'GET':
        def auth_status(user):
            if user.is_authenticated:
                return True
            else:
                return False
        user_auth = await sync_to_async(auth_status)(request.user)
        form = UserLoginForm()
        context = {'form': form,'user_auth': user_auth}
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