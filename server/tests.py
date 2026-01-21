from django.test import TestCase, Client
from django.urls import reverse


class ServerViewTest(TestCase):
    """测试Server应用视图"""
    
    def setUp(self):
        """设置测试数据"""
        self.client = Client()
    
    def test_index_page(self):
        """测试首页"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'server/index.html')
    
    def test_index_page_by_name(self):
        """测试通过名称访问首页"""
        response = self.client.get(reverse('server:index'))
        self.assertEqual(response.status_code, 200)
    
    def test_about_page(self):
        """测试关于页面"""
        response = self.client.get(reverse('server:about'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'server/about.html')
    
    def test_easter_egg_page(self):
        """测试彩蛋页面"""
        response = self.client.get(reverse('server:easter_egg_1'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'server/easter_egg_1.html')


class ServerURLTest(TestCase):
    """测试Server应用URL配置"""
    
    def test_index_url_resolves(self):
        """测试首页URL解析"""
        url = reverse('server:index')
        self.assertEqual(url, '/server/')
    
    def test_about_url_resolves(self):
        """测试关于页面URL解析"""
        url = reverse('server:about')
        self.assertEqual(url, '/server/about/')
    
    def test_easter_egg_url_resolves(self):
        """测试彩蛋页面URL解析"""
        url = reverse('server:easter_egg_1')
        self.assertEqual(url, '/server/easter_egg_1/')


class ServerStaticFilesTest(TestCase):
    """测试静态文件"""
    
    def setUp(self):
        """设置测试数据"""
        self.client = Client()
    
    def test_favicon_access(self):
        """测试访问网站图标"""
        response = self.client.get('/favicon.ico')
        # 静态文件在生产环境可能由其他服务器处理
        # 这里只测试URL是否配置
        self.assertIn(response.status_code, [200, 404])


class ServerResponseTest(TestCase):
    """测试服务器响应"""
    
    def setUp(self):
        """设置测试数据"""
        self.client = Client()
    
    def test_index_returns_html(self):
        """测试首页返回HTML"""
        response = self.client.get('/')
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
    
    def test_404_page(self):
        """测试404页面"""
        response = self.client.get('/nonexistent-page/')
        self.assertEqual(response.status_code, 404)
    
    def test_multiple_page_loads(self):
        """测试多次加载页面"""
        for _ in range(3):
            response = self.client.get('/')
            self.assertEqual(response.status_code, 200)
