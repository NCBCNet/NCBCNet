import hashlib
import hmac
import time

from django.conf import settings
from django.http import FileResponse
from rest_framework import generics, permissions, status, parsers
from rest_framework.response import Response
from rest_framework.views import APIView

from file_save.serializers import FolderSerializer, FileSerializer, FileUploadSerializer
from file_save.services import (
    delete_file,
    delete_folder,
    get_downloadable_file,
    get_file,
    list_files,
    list_folders,
    list_shared_files,
    toggle_share,
)

# 签名下载链接有效期（秒）
DOWNLOAD_LINK_TTL = int(getattr(settings, 'DOWNLOAD_LINK_TTL', 300))


def _sign_download(file_id, exp):
    """用 SECRET_KEY 对 (file_id, exp) 生成 HMAC-SHA256 签名。"""
    message = f"{file_id}:{exp}".encode('utf-8')
    return hmac.new(settings.SECRET_KEY.encode('utf-8'), message, hashlib.sha256).hexdigest()


class FolderListView(generics.ListCreateAPIView):
    """文件夹列表/创建（不分页，前端网格直接消费数组）"""
    serializer_class = FolderSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        parent_id = self.request.query_params.get('parent')
        return list_folders(user, parent_id=parent_id)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class FolderDeleteView(generics.DestroyAPIView):
    """删除文件夹"""
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        delete_folder(request.user, self.kwargs['pk'])
        return Response({'success': True, 'message': '文件夹已删除'})


class FileListView(generics.ListAPIView):
    """文件列表（不分页，前端网格直接消费数组）"""
    serializer_class = FileSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        folder_id = self.request.query_params.get('folder')

        # 获取共享文件
        shared = self.request.query_params.get('shared', '')
        if shared == 'true':
            return list_files(user, shared=True)

        return list_files(user, folder_id=folder_id)


class FileUploadView(generics.CreateAPIView):
    """文件上传"""
    serializer_class = FileUploadSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        uploaded_file = self.request.FILES.get('file')
        serializer.save(
            owner=self.request.user,
            original_name=uploaded_file.name,
            file_size=uploaded_file.size,
        )


class FileDeleteView(generics.DestroyAPIView):
    """删除文件"""
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        delete_file(request.user, self.kwargs['pk'])
        return Response({'success': True, 'message': '文件已删除'})


class FileShareToggleView(APIView):
    """切换文件共享状态"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        file_instance = toggle_share(request.user, pk)
        return Response({
            'success': True,
            'share': file_instance.share,
            'message': '共享状态已更新'
        })


class SharedFileListView(generics.ListAPIView):
    """共享文件列表（其他用户共享的文件，不分页；公开可访问）。"""
    serializer_class = FileSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        return list_shared_files(self.request.user)


class FileDownloadUrlView(APIView):
    """获取签名下载链接。

    共享文件公开可下载（匿名亦可）；私有文件仅所有者（需登录）。
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        file_instance = get_file(pk)

        # 私有文件：仅所有者；共享文件：任何人
        if not file_instance.share:
            if not request.user.is_authenticated:
                raise PermissionDenied('请先登录后下载私有文件')
            if file_instance.owner_id != request.user.id:
                raise PermissionDenied('无权下载该文件')

        exp = int(time.time()) + DOWNLOAD_LINK_TTL
        token = _sign_download(pk, exp)
        url = request.build_absolute_uri(f'/api/v1/files/{pk}/download/?exp={exp}&sig={token}')
        return Response({'url': url, 'expires_in': DOWNLOAD_LINK_TTL})


class FileDownloadView(APIView):
    """签名校验通过后流式下载文件。

    下载链接本身即授权凭证（HMAC 签名 + 过期时间），故无需 Cookie/登录态，
    支持前端用普通 <a href> 触发下载。
    """

    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        exp = request.query_params.get('exp')
        sig = request.query_params.get('sig')

        if not exp or not sig:
            return Response(
                {'code': 'invalid_link', 'message': '下载链接无效'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            exp = int(exp)
        except (TypeError, ValueError):
            return Response(
                {'code': 'invalid_link', 'message': '下载链接无效'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if exp < int(time.time()):
            return Response(
                {'code': 'link_expired', 'message': '下载链接已过期'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not hmac.compare_digest(sig, _sign_download(pk, exp)):
            return Response(
                {'code': 'invalid_link', 'message': '下载链接无效'},
                status=status.HTTP_403_FORBIDDEN,
            )

        file_instance = get_file(pk)
        try:
            file_handle = file_instance.file.open('rb')
        except Exception:
            return Response(
                {'code': 'not_found', 'message': '文件不存在或已被删除'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return FileResponse(
            file_handle,
            as_attachment=True,
            filename=file_instance.original_name,
            content_type='application/octet-stream',
        )
