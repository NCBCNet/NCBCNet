from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.middleware.csrf import get_token, rotate_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from api.authentication import set_auth_cookies, clear_auth_cookies
from api.throttles import LoginRateThrottle, RegisterRateThrottle
from usermanage.serializers import (
    LoginSerializer,
    ProfileSerializer,
    RegisterSerializer,
    UserProfileSerializer,
    UserSerializer,
)
from usermanage.services import (
    delete_user,
    get_or_create_profile,
    update_profile,
)


class CsrfCookieView(APIView):
    """下发 csrftoken Cookie，供 SPA 读取后回填 X-CSRFToken 请求头。"""

    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        return Response({'csrfToken': get_token(request)})


class LoginView(APIView):
    """登录：校验账号密码，写入 HttpOnly Cookie。"""

    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        refresh = RefreshToken.for_user(user)
        response = Response({
            'success': True,
            'message': '登录成功',
            'user': UserSerializer(user).data,
        })
        set_auth_cookies(response, refresh.access_token, refresh)
        # 登录成功后轮换 CSRF token（防 login CSRF）
        rotate_token(request)
        return response


class RefreshView(APIView):
    """刷新 access token（读取 refresh Cookie，轮换签发）。"""

    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        raw = request.COOKIES.get(settings.AUTH_COOKIE_REFRESH)
        if not raw:
            return Response(
                {'code': 'not_authenticated', 'message': '未登录或登录已过期'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            old_refresh = RefreshToken(raw)
            User = get_user_model()
            user = User.objects.get(id=old_refresh['user_id'])
            refresh = RefreshToken.for_user(user)
        except Exception:
            return Response(
                {'code': 'not_authenticated', 'message': '登录已过期，请重新登录'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        response = Response({'success': True})
        set_auth_cookies(response, refresh.access_token, refresh)
        return response


class LogoutView(APIView):
    """登出：清除 access / refresh Cookie。"""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        response = Response({'success': True, 'message': '已退出登录'})
        return clear_auth_cookies(response)


class RegisterView(generics.CreateAPIView):
    """用户注册：创建用户后自动登录（写入 Cookie）。"""

    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer
    throttle_classes = [RegisterRateThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # RegisterSerializer.create -> usermanage.services.register_user
        # （用户 + Profile 在服务层事务内创建）
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        response = Response({
            'success': True,
            'message': '注册成功',
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)
        set_auth_cookies(response, refresh.access_token, refresh)
        return response


class UserDetailView(generics.RetrieveUpdateAPIView):
    """获取/更新当前用户信息。"""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()

        # 更新 Profile 字段：优先嵌套 profile，支持顶层 avatar 直传
        profile_data = request.data.get('profile', {})
        if not isinstance(profile_data, dict):
            profile_data = {}
        if 'avatar' in request.FILES:
            profile_data = dict(profile_data)
            profile_data['avatar'] = request.FILES['avatar']

        # 校验仍由序列化器负责，ORM 写入收敛到 usermanage.services.update_profile
        profile = get_or_create_profile(user)
        if profile_data:
            profile_serializer = ProfileSerializer(profile, data=profile_data, partial=True)
            profile_serializer.is_valid(raise_exception=True)
            profile_data = profile_serializer.validated_data

        if 'email' in request.data:
            # email 显式出现（含 null）才写 User 字段
            update_profile(user, profile_data=profile_data, email=request.data['email'])
        else:
            update_profile(user, profile_data=profile_data)

        return Response(UserProfileSerializer(user).data)


class UserDeleteView(generics.DestroyAPIView):
    """删除当前用户。"""

    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        # 删除用户（Profile 等级联对象在服务层事务内一并删除）
        delete_user(user)
        response = Response({'success': True, 'message': '用户已删除'}, status=status.HTTP_200_OK)
        return clear_auth_cookies(response)


class CheckAuthView(APIView):
    """检查当前登录状态（并在响应中确保 CSRF Cookie 已下发）。"""

    permission_classes = [permissions.IsAuthenticated]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        return Response({
            'is_authenticated': True,
            'user': UserSerializer(request.user).data,
        })
