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
    
    def delete(self, *args, **kwargs):
        """重写删除方法，确保删除文件夹时也删除其中的所有物理文件"""
        # 1. 递归删除所有子文件夹中的文件
        for subfolder in self.subfolders.all():
            subfolder.delete()  # 递归调用，会删除子文件夹的文件
        
        # 2. 删除当前文件夹中的所有文件（物理文件）
        for file in self.files.all():
            # 删除物理文件
            if file.file:
                try:
                    file.file.delete(save=False)  # save=False 防止再次保存数据库
                except Exception as e:
                    # 如果文件已经不存在，继续删除数据库记录
                    pass
            # 删除数据库记录
            file.delete()
        
        # 3. 最后删除文件夹本身的数据库记录
        super().delete(*args, **kwargs)

class UploadedFile(models.Model):
    STATUS_CHOICES = [
        ('processing', '处理中'),
        ('done', '完成'),
        ('failed', '失败'),
    ]

    file = models.FileField(upload_to='uploads/')
    original_name = models.CharField(max_length=255)
    folder = models.ForeignKey(Folder, null=True, blank=True, on_delete=models.CASCADE, related_name='files')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='files')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.BigIntegerField(default=0)
    share = models.BooleanField(default=False)
    # 后处理状态（RQ worker 异步处理，默认 done 兼容存量记录）
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='done')
    # 图片缩略图（后处理生成）
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True)
    # 文件校验和（完整性/去重）
    sha256 = models.CharField(max_length=64, blank=True)
    
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