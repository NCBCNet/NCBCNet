"""file_save 序列化器（从 api/serializers/files.py 迁移，类名与字段保持不变）。

ORM 写入收敛到 file_save.services（create_folder / upload_file）。
"""
from rest_framework import serializers

from file_save.models import Folder, UploadedFile
from file_save.services import create_folder, upload_file


class FolderSerializer(serializers.ModelSerializer):
    """文件夹序列化器"""
    has_children = serializers.SerializerMethodField()

    class Meta:
        model = Folder
        fields = ['id', 'name', 'parent', 'parent_id', 'created_at', 'has_children']
        read_only_fields = ['id', 'created_at']

    def get_has_children(self, obj):
        return obj.subfolders.exists()

    def create(self, validated_data):
        return create_folder(
            user=validated_data.pop('owner'),
            name=validated_data['name'],
            parent=validated_data.get('parent'),
        )


class FileSerializer(serializers.ModelSerializer):
    """文件序列化器"""
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    file_size_display = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = UploadedFile
        fields = [
            'id', 'file', 'original_name', 'folder', 'owner', 'owner_username',
            'uploaded_at', 'file_size', 'file_size_display', 'share', 'download_url'
        ]
        read_only_fields = ['id', 'owner', 'uploaded_at', 'file_size']

    def get_file_size_display(self, obj):
        return obj.get_file_size_display()

    def get_download_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/file_up/file_download/{obj.id}/')
        return f'/file_up/file_download/{obj.id}/'


class FileUploadSerializer(serializers.ModelSerializer):
    """文件上传序列化器"""
    class Meta:
        model = UploadedFile
        fields = ['file', 'folder']

    def create(self, validated_data):
        return upload_file(
            user=validated_data.pop('owner'),
            file_obj=validated_data.pop('file'),
            folder=validated_data.pop('folder', None),
            original_name=validated_data.pop('original_name', None),
            file_size=validated_data.pop('file_size', 0),
        )
