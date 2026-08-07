from rest_framework import generics, permissions, status, parsers
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.http import Http404

from file_save.models import Folder, UploadedFile
from api.serializers.files import FolderSerializer, FileSerializer, FileUploadSerializer


class FolderListView(generics.ListCreateAPIView):
    """文件夹列表/创建"""
    serializer_class = FolderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        parent_id = self.request.query_params.get('parent')
        if parent_id:
            return Folder.objects.filter(owner=user, parent_id=parent_id)
        return Folder.objects.filter(owner=user, parent=None)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class FolderDeleteView(generics.DestroyAPIView):
    """删除文件夹"""
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Folder.objects.filter(owner=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({'success': True, 'message': '文件夹已删除'})


class FileListView(generics.ListAPIView):
    """文件列表"""
    serializer_class = FileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        folder_id = self.request.query_params.get('folder')

        # 获取共享文件
        shared = self.request.query_params.get('shared', '')
        if shared == 'true':
            return UploadedFile.objects.filter(share=True).exclude(owner=user)

        if folder_id:
            return UploadedFile.objects.filter(owner=user, folder_id=folder_id)
        return UploadedFile.objects.filter(owner=user, folder=None)


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

    def get_queryset(self):
        return UploadedFile.objects.filter(owner=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # 删除物理文件
        if instance.file:
            instance.file.delete(save=False)
        instance.delete()
        return Response({'success': True, 'message': '文件已删除'})


class FileShareToggleView(APIView):
    """切换文件共享状态"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            file_instance = UploadedFile.objects.get(pk=pk, owner=request.user)
            file_instance.share = not file_instance.share
            file_instance.save(update_fields=['share'])
            return Response({
                'success': True,
                'share': file_instance.share,
                'message': '共享状态已更新'
            })
        except UploadedFile.DoesNotExist:
            raise Http404('文件不存在')


class SharedFileListView(generics.ListAPIView):
    """共享文件列表（其他用户共享的文件）"""
    serializer_class = FileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UploadedFile.objects.filter(share=True).exclude(owner=self.request.user)
