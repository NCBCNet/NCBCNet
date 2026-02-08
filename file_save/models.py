from django.db import models
from django.contrib.auth.models import User
import os

# Create your models here.
class Folder(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='subfolders')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='folders')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['name', 'parent', 'owner']
    
    def __str__(self):
        return self.name
    
    def get_path(self):
        """返回文件夹的完整路径"""
        if self.parent:
            return os.path.join(self.parent.get_path(), self.name)
        return self.name

class UploadedFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    original_name = models.CharField(max_length=255)
    folder = models.ForeignKey(Folder, null=True, blank=True, on_delete=models.CASCADE, related_name='files')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='files')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.BigIntegerField(default=0)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.original_name
    
    def get_file_size_display(self):
        """返回人类可读的文件大小"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"