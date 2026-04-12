from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Profile


class ProfileModelTest(TestCase):
    """测试Profile模型"""
    
    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.profile = Profile.objects.create(
            user=self.user,
            phone='13800138000',
            bio='这是测试用户的简介'
        )
    
    def test_profile_creation(self):
        """测试用户资料创建"""
        self.assertTrue(isinstance(self.profile, Profile))
        self.assertEqual(self.profile.user, self.user)
    
    def test_profile_str(self):
        """测试用户资料字符串表示"""
        expected = f'user {self.user.username}'
        self.assertEqual(str(self.profile), expected)
    
    def test_profile_fields(self):
        """测试用户资料字段"""
        self.assertEqual(self.profile.phone, '13800138000')
        self.assertEqual(self.profile.bio, '这是测试用户的简介')
    
    def test_profile_user_relation(self):
        """测试用户资料与用户的关系"""
        self.assertEqual(self.user.profile, self.profile)


class UserRegistrationTest(TestCase):
    """测试用户注册"""
    
    def setUp(self):
        """设置测试数据"""
        self.client = Client()
        self.register_url = reverse('usermanage:register')
    
    # def test_register_page_get(self):
    #     """测试访问注册页面"""
    #     response = self.client.get(self.register_url)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertContains(response, 'form')
    #
    def test_register_new_user(self):
        """测试注册新用户"""
        initial_user_count = User.objects.count()
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password2': 'newpass123'
        })
        
        # 检查用户是否创建
        self.assertEqual(User.objects.count(), initial_user_count + 1)
        
        # 检查新用户信息
        new_user = User.objects.get(username='newuser')
        self.assertEqual(new_user.email, 'newuser@example.com')
        self.assertTrue(new_user.check_password('newpass123'))
    
    def test_register_duplicate_username(self):
        """测试注册重复用户名"""
        User.objects.create_user(
            username='existinguser',
            password='pass123'
        )
        response = self.client.post(self.register_url, {
            'username': 'existinguser',
            'email': 'new@example.com',
            'password': 'pass123',
            'password2': 'pass123'
        })
        self.assertEqual(response.status_code, 400)


class UserLoginTest(TestCase):
    """测试用户登录"""
    
    def setUp(self):
        """设置测试数据"""
        self.client = Client()
        self.login_url = reverse('usermanage:login')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_login_page_get(self):
        """测试访问登录页面"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
    
    def test_login_valid_credentials(self):
        """测试有效凭证登录"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        # 检查是否重定向
        self.assertEqual(response.status_code, 302)
        
        # 检查用户是否已登录
        user = User.objects.get(username='testuser')
        self.assertTrue(
            '_auth_user_id' in self.client.session
        )
    
    def test_login_invalid_credentials(self):
        """测试无效凭证登录"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertContains(response, '账号或密码有误')
    
    def test_login_nonexistent_user(self):
        """测试不存在的用户登录"""
        response = self.client.post(self.login_url, {
            'username': 'nonexistent',
            'password': 'somepass123'
        })
        self.assertContains(response, '账号或密码有误')


class UserLogoutTest(TestCase):
    """测试用户登出"""
    
    def setUp(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_logout(self):
        """测试用户登出"""
        # 确认用户已登录
        self.assertTrue('_auth_user_id' in self.client.session)
        
        # 登出
        response = self.client.get(reverse('usermanage:logout'))
        
        # 检查是否重定向
        self.assertEqual(response.status_code, 302)


class ProfileEditTest(TestCase):
    """测试编辑用户资料"""
    
    def setUp(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_edit_profile_page_get(self):
        """测试访问编辑资料页面"""
        response = self.client.get(
            reverse('usermanage:edit_profile', args=[self.user.id])
        )
        self.assertEqual(response.status_code, 200)
    
    def test_edit_profile_create_if_not_exists(self):
        """测试自动创建不存在的资料"""
        self.assertFalse(
            Profile.objects.filter(user=self.user).exists()
        )
        response = self.client.get(
            reverse('usermanage:edit_profile', args=[self.user.id])
        )
        self.assertEqual(response.status_code, 200)
        # 访问后应该创建了profile
        self.assertTrue(
            Profile.objects.filter(user=self.user).exists()
        )
    
    def test_edit_profile_update(self):
        """测试更新用户资料"""
        profile = Profile.objects.create(user=self.user)
        
        response = self.client.post(
            reverse('usermanage:edit_profile', args=[self.user.id]),
            {
                'phone': '13900139000',
                'bio': '更新后的简介'
            }
        )
        
        # 刷新profile
        profile.refresh_from_db()
        self.assertEqual(profile.phone, '13900139000')
        self.assertEqual(profile.bio, '更新后的简介')
    
    def test_edit_other_user_profile(self):
        """测试编辑其他用户的资料"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )
        Profile.objects.create(user=other_user)
        
        response = self.client.post(
            reverse('usermanage:edit_profile', args=[other_user.id]),
            {
                'phone': '13900139000',
                'bio': '尝试修改他人资料'
            }
        )
        self.assertContains(response, '你没有权限')


class UserDeleteTest(TestCase):
    """测试删除用户"""
    
    def setUp(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_delete_own_account(self):
        """测试删除自己的账号"""
        initial_user_count = User.objects.count()
        response = self.client.post(
            reverse('usermanage:delete', args=[self.user.id])
        )
        
        # 检查重定向
        self.assertEqual(response.status_code, 302)
        
        # 检查用户是否被删除
        self.assertEqual(User.objects.count(), initial_user_count - 1)
        self.assertFalse(
            User.objects.filter(username='testuser').exists()
        )
    
    def test_delete_other_user_account(self):
        """测试删除其他用户的账号"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )
        
        response = self.client.post(
            reverse('usermanage:delete', args=[other_user.id])
        )
        self.assertContains(response, '你没有删除权限')
        
        # 确认其他用户未被删除
        self.assertTrue(
            User.objects.filter(username='otheruser').exists()
        )
    
    def test_delete_not_logged_in(self):
        """测试未登录时删除账号"""
        self.client.logout()
        response = self.client.post(
            reverse('usermanage:delete', args=[self.user.id])
        )
        # 应该重定向到登录页
        self.assertEqual(response.status_code, 302)
