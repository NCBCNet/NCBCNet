from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from .models import UploadedFile, Folder
import os
import tempfile

# Common test settings decorator
test_settings = override_settings(
    MEDIA_ROOT=tempfile.mkdtemp(),
    CACHES={
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://localhost:6379/0',
            'OPTIONS': {
                'REDIS_CLIENT_CLASS': 'fakeredis.FakeRedis',
            }
        }
    },
    SESSION_ENGINE='django.contrib.sessions.backends.db',
    RATELIMIT_ENABLE=False
)


@test_settings
class FileSaveAppTest(TestCase):
    """测试FileSave应用"""
    
    def setUp(self):
        """设置测试数据"""
        self.client = Client()
    
    def test_file_save_app_installed(self):
        """测试FileSave应用是否正确安装"""
        from django.apps import apps
        self.assertTrue(apps.is_installed('file_save'))
    
    def test_file_save_app_ready(self):
        """测试FileSave应用是否准备就绪"""
        from django.apps import apps
        app_config = apps.get_app_config('file_save')
        self.assertEqual(app_config.name, 'file_save')


@test_settings
class FolderModelTest(TestCase):
    """测试文件夹模型"""
    
    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_create_folder(self):
        """测试创建文件夹"""
        folder = Folder.objects.create(
            name='Test Folder',
            owner=self.user
        )
        self.assertEqual(folder.name, 'Test Folder')
        self.assertEqual(folder.owner, self.user)
        self.assertIsNone(folder.parent)
    
    def test_create_subfolder(self):
        """测试创建子文件夹"""
        parent = Folder.objects.create(
            name='Parent Folder',
            owner=self.user
        )
        child = Folder.objects.create(
            name='Child Folder',
            parent=parent,
            owner=self.user
        )
        self.assertEqual(child.parent, parent)
        # self.assertEqual(child.get_path(), 'Parent Folder/Child Folder')
    
    def test_folder_cascade_delete(self):
        """测试文件夹级联删除"""
        parent = Folder.objects.create(
            name='Parent',
            owner=self.user
        )
        child = Folder.objects.create(
            name='Child',
            parent=parent,
            owner=self.user
        )
        
        # 创建文件
        test_file = SimpleUploadedFile(
            "test.txt",
            b"Test content",
            content_type="text/plain"
        )
        uploaded_file = UploadedFile.objects.create(
            file=test_file,
            original_name='test.txt',
            folder=child,
            owner=self.user,
            file_size=12
        )
        
        # 删除父文件夹应该级联删除子文件夹和文件
        parent.delete()
        
        self.assertEqual(Folder.objects.count(), 0)
        self.assertEqual(UploadedFile.objects.count(), 0)


@test_settings
class FileModelTest(TestCase):
    """测试文件模型"""
    
    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_create_file(self):
        """测试创建文件"""
        test_file = SimpleUploadedFile(
            "test.txt",
            b"Test content",
            content_type="text/plain"
        )
        uploaded_file = UploadedFile.objects.create(
            file=test_file,
            original_name='test.txt',
            owner=self.user,
            file_size=12
        )
        self.assertEqual(uploaded_file.original_name, 'test.txt')
        self.assertEqual(uploaded_file.file_size, 12)
        self.assertFalse(uploaded_file.share)
    
    def test_file_size_display(self):
        """测试文件大小显示"""
        test_file = SimpleUploadedFile(
            "test.txt",
            b"Test content",
            content_type="text/plain"
        )
        uploaded_file = UploadedFile.objects.create(
            file=test_file,
            original_name='test.txt',
            owner=self.user,
            file_size=1024
        )
        self.assertEqual(uploaded_file.get_file_size_display(), '1.0 KB')
        
        uploaded_file.file_size = 1024 * 1024
        self.assertEqual(uploaded_file.get_file_size_display(), '1.0 MB')


@test_settings
class FolderViewTest(TestCase):
    """测试文件夹视图"""
    
    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_folder_create(self):
        """测试创建文件夹"""
        response = self.client.post(reverse('file_save:folder_create'), {
            'name': 'New Folder'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertEqual(Folder.objects.count(), 1)
        folder = Folder.objects.first()
        self.assertEqual(folder.name, 'New Folder')
        self.assertEqual(folder.owner, self.user)
    
    def test_folder_delete(self):
        """测试删除文件夹"""
        folder = Folder.objects.create(
            name='Test Folder',
            owner=self.user
        )
        response = self.client.post(
            reverse('file_save:folder_delete', args=[folder.id])
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertEqual(Folder.objects.count(), 0)


@test_settings
class FileViewTest(TestCase):
    """测试文件视图"""
    
    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_file_upload(self):
        """测试文件上传"""
        test_file = SimpleUploadedFile(
            "test.txt",
            b"Test content",
            content_type="text/plain"
        )
        response = self.client.post(
            reverse('file_save:file_upload'),
            {
                'file': test_file,
                'folder': ''
            }
        )
        self.assertEqual(response.status_code, 200)
        # Check JSON response
        json_data = response.json()
        self.assertTrue(json_data['success'])
        self.assertEqual(UploadedFile.objects.count(), 1)
        uploaded = UploadedFile.objects.first()
        self.assertEqual(uploaded.original_name, 'test.txt')
    
    def test_file_delete(self):
        """测试文件删除"""
        test_file = SimpleUploadedFile(
            "test.txt",
            b"Test content",
            content_type="text/plain"
        )
        uploaded_file = UploadedFile.objects.create(
            file=test_file,
            original_name='test.txt',
            owner=self.user,
            file_size=12
        )
        response = self.client.post(
            reverse('file_save:file_delete', args=[uploaded_file.id])
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertEqual(UploadedFile.objects.count(), 0)
    
    def test_file_download(self):
        """测试文件下载"""
        test_file = SimpleUploadedFile(
            "test.txt",
            b"Test content",
            content_type="text/plain"
        )
        uploaded_file = UploadedFile.objects.create(
            file=test_file,
            original_name='test.txt',
            owner=self.user,
            file_size=12
        )
        response = self.client.get(
            reverse('file_save:file_download', args=[uploaded_file.id])
        )
        self.assertEqual(response.status_code, 200)


@test_settings
class FileShareTest(TestCase):
    """测试文件分享功能"""
    
    def setUp(self):
        """设置测试数据"""
        self.user1 = User.objects.create_user(
            username='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='testpass123'
        )
    
    def test_file_share_toggle(self):
        """测试文件分享开关"""
        self.client.login(username='user1', password='testpass123')
        
        test_file = SimpleUploadedFile(
            "test.txt",
            b"Test content",
            content_type="text/plain"
        )
        uploaded_file = UploadedFile.objects.create(
            file=test_file,
            original_name='test.txt',
            owner=self.user1,
            file_size=12,
            share=False
        )
        
        # Toggle share on
        response = self.client.post(
            reverse('file_save:file_list'),
            {
                'shared_target': uploaded_file.id
            }
        )
        self.assertEqual(response.status_code, 302)
        uploaded_file.refresh_from_db()
        self.assertTrue(uploaded_file.share)
    
    def test_shared_file_download_by_other_user(self):
        """测试其他用户下载共享文件"""
        # User1 creates and shares a file
        test_file = SimpleUploadedFile(
            "test.txt",
            b"Test content",
            content_type="text/plain"
        )
        uploaded_file = UploadedFile.objects.create(
            file=test_file,
            original_name='test.txt',
            owner=self.user1,
            file_size=12,
            share=True
        )
        
        # User2 tries to download
        self.client.login(username='user2', password='testpass123')
        response = self.client.get(
            reverse('file_save:file_download', args=[uploaded_file.id])
        )
        self.assertEqual(response.status_code, 200)  # Should succeed
