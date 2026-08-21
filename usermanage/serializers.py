"""usermanage 序列化器（从 api/serializers/auth.py 迁移，类名与字段保持不变）。

ORM 写入收敛到 usermanage.services（register_user）。
"""
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers

from usermanage.models import Profile
from usermanage.services import register_user


class LoginSerializer(serializers.Serializer):
    """登录序列化器（校验账号密码，返回 user）。"""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        user = authenticate(username=attrs['username'], password=attrs['password'])
        if user is None:
            raise serializers.ValidationError('账号或密码错误')
        if not user.is_active:
            raise serializers.ValidationError('该账号已被禁用')
        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """用户基本信息序列化器"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class RegisterSerializer(serializers.ModelSerializer):
    """用户注册序列化器"""
    password = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True, min_length=6, label='确认密码')

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'password2']

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('用户名已存在')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password2': '两次输入的密码不一致'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        return register_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', ''),
        )


class ProfileSerializer(serializers.ModelSerializer):
    """用户资料序列化器"""
    class Meta:
        model = Profile
        fields = ['phone', 'avatar', 'bio']


class UserProfileSerializer(serializers.ModelSerializer):
    """用户完整信息（含资料）序列化器"""
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined', 'profile']
        read_only_fields = ['id', 'date_joined']
