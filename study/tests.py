from django.test import TestCase, Client
from django.contrib.auth.models import User


class StudyAppTest(TestCase):
    """测试Study应用"""
    
    def setUp(self):
        """设置测试数据"""
        self.client = Client()
    
    def test_study_app_installed(self):
        """测试Study应用是否正确安装"""
        from django.apps import apps
        self.assertTrue(apps.is_installed('study'))
    
    def test_study_app_ready(self):
        """测试Study应用是否准备就绪"""
        from django.apps import apps
        app_config = apps.get_app_config('study')
        self.assertEqual(app_config.name, 'study')


class StudyModelTest(TestCase):
    """测试Study模型（为将来的功能预留）"""
    
    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_user_exists_for_study(self):
        """测试用户可用于学习功能"""
        self.assertTrue(User.objects.filter(username='testuser').exists())
        user = User.objects.get(username='testuser')
        self.assertEqual(user.username, 'testuser')
