from rest_framework import serializers
from file_save.models import Folder, UploadedFile


class FolderSerializer(serializers.ModelSerializer):
    """文件夹序列化器"""
    has_children = serializers.SerializerMethodField()

    class Meta:
        model = Folder
        fields = ['id', 'name', 'parent', 'parent_id', 'created_at', 'has_children']
        read_only_fields = ['id', 'created_at']

    def get_has_children(self, obj):
        return obj.subfolders.exists()


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
