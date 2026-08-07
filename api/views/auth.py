from django.contrib.auth.models import User
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from api.serializers.auth import (
    RegisterSerializer,
    UserSerializer,
    UserProfileSerializer,
    ProfileSerializer,
)
from usermanage.models import Profile


class RegisterView(generics.CreateAPIView):
    """用户注册"""
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # 自动创建 Profile
        Profile.objects.get_or_create(user=user)

        # 生成 JWT token
        refresh = RefreshToken.for_user(user)
        return Response({
            'success': True,
            'message': '注册成功',
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)


class UserDetailView(generics.RetrieveUpdateAPIView):
    """获取/更新当前用户信息"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        profile, _ = Profile.objects.get_or_create(user=user)

        # 更新 Profile 字段
        profile_data = request.data.get('profile', {})
        profile_serializer = ProfileSerializer(profile, data=profile_data, partial=True)
        if profile_serializer.is_valid():
            profile_serializer.save()

        # 更新 User 字段
        if 'email' in request.data:
            user.email = request.data['email']
            user.save()

        return Response(UserProfileSerializer(user).data)


class UserDeleteView(generics.DestroyAPIView):
    """删除当前用户"""
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        user.delete()
        return Response({'success': True, 'message': '用户已删除'}, status=status.HTTP_200_OK)


class CheckAuthView(APIView):
    """检查当前登录状态"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({
            'is_authenticated': True,
            'user': UserSerializer(request.user).data
        })
