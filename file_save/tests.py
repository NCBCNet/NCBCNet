from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile


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


class FileHandlingTest(TestCase):
    """测试文件处理功能（为将来的功能预留）"""
    
    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_create_simple_uploaded_file(self):
        """测试创建简单上传文件对象"""
        test_file = SimpleUploadedFile(
            "test_file.txt",
            b"This is test file content",
            content_type="text/plain"
        )
        self.assertEqual(test_file.name, "test_file.txt")
        self.assertEqual(test_file.size, 25)
    
    def test_create_image_file(self):
        """测试创建图片文件对象"""
        # 创建一个简单的1x1像素PNG图片
        image_data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
            b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
            b'\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        test_image = SimpleUploadedFile(
            "test_image.png",
            image_data,
            content_type="image/png"
        )
        self.assertEqual(test_image.name, "test_image.png")
        self.assertEqual(test_image.content_type, "image/png")
