from time import sleep

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from .models import Article, ArticleColumn


class ArticleColumnModelTest(TestCase):
    """测试ArticleColumn模型"""

    def setUp(self):
        """设置测试数据"""
        self.column = ArticleColumn.objects.create(
            title='技术专栏',
            created=timezone.now()
        )

    def test_column_creation(self):
        """测试专栏创建"""
        self.assertTrue(isinstance(self.column, ArticleColumn))
        self.assertEqual(self.column.__str__(), self.column.title)

    def test_column_title(self):
        """测试专栏标题"""
        self.assertEqual(self.column.title, '技术专栏')


class ArticleModelTest(TestCase):
    """测试Article模型"""

    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.column = ArticleColumn.objects.create(
            title='测试专栏'
        )
        self.article = Article.objects.create(
            author=self.user,
            title='测试文章标题',
            content='这是一篇测试文章的内容',
            column=self.column,
            likes=0,
            total_views=0
        )

    def test_article_creation(self):
        """测试文章创建"""
        self.assertTrue(isinstance(self.article, Article))
        self.assertEqual(self.article.__str__(), self.article.title)

    def test_article_content(self):
        """测试文章内容"""
        self.assertEqual(self.article.title, '测试文章标题')
        self.assertEqual(self.article.content, '这是一篇测试文章的内容')
        self.assertEqual(self.article.author.username, 'testuser')

    def test_article_column_relation(self):
        """测试文章与专栏的关系"""
        self.assertEqual(self.article.column, self.column)
        self.assertIn(self.article, self.column.article.all())

    def test_article_get_absolute_url(self):
        """测试文章URL"""
        url = self.article.get_absolute_url()
        self.assertEqual(url, reverse('article:article_detail', args=[self.article.id]))

    def test_article_ordering(self):
        sleep(0.01)  # 确保创建时间不同
        """测试文章排序"""
        article2 = Article.objects.create(
            author=self.user,
            title='第二篇文章',
            content='第二篇文章内容'
        )
        articles = Article.objects.all()
        self.assertEqual(articles[0], article2)
        self.assertEqual(articles[1], self.article)


class ArticleViewTest(TestCase):
    """测试Article视图"""
    
    def setUp(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.column = ArticleColumn.objects.create(title='测试专栏')
        self.article = Article.objects.create(
            author=self.user,
            title='测试文章',
            content='# 测试内容\n\n这是测试文章的内容',
            column=self.column
        )
    
    def test_article_list_view(self):
        """测试文章列表视图"""
        response = self.client.get(reverse('article:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.article.title)
    
    def test_article_detail_view(self):
        """测试文章详情视图"""
        initial_views = self.article.total_views
        response = self.client.get(
            reverse('article:article_detail', args=[self.article.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.article.title)
        
        # 检查浏览次数是否增加
        self.article.refresh_from_db()
        self.assertEqual(self.article.total_views, initial_views + 1)
    
    def test_article_create_view_not_logged_in(self):
        """测试未登录用户访问创建文章页面"""
        response = self.client.get(reverse('article:article_create'))
        self.assertEqual(response.status_code, 302)  # 重定向到登录页
    
    def test_article_create_view_logged_in(self):
        """测试已登录用户访问创建文章页面"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('article:article_create'))
        self.assertEqual(response.status_code, 200)
    
    def test_article_update_view_not_author(self):
        """测试非作者更新文章"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )
        self.client.login(username='otheruser', password='otherpass123')
        response = self.client.get(
            reverse('article:article_update', args=[self.article.id])
        )
        self.assertEqual(response.status_code, 302)
    
    def test_article_delete_view_author(self):
        """测试作者删除文章"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('article:article_delete', args=[self.article.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Article.objects.filter(id=self.article.id).exists()
        )
    
    
    def test_article_list_order_by_views(self):
        """测试按浏览量排序"""
        article2 = Article.objects.create(
            author=self.user,
            title='高浏览量文章',
            content='内容',
            total_views=100
        )
        response = self.client.get(
            reverse('article:list') + '?order=total_views'
        )
        self.assertEqual(response.status_code, 200)
    
    def test_article_list_filter_by_column(self):
        """测试按专栏筛选"""
        response = self.client.get(
            reverse('article:list') + f'?column={self.column.id}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.article.title)


class ArticleLikesTest(TestCase):
    """测试文章点赞功能"""
    
    def setUp(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.article = Article.objects.create(
            author=self.user,
            title='测试文章',
            content='内容',
            likes=0
        )
    
    def test_increase_likes(self):
        """测试增加点赞数"""
        initial_likes = self.article.likes
        response = self.client.post(
            reverse('article:increase_likes', args=[self.article.id])
        )
        self.assertEqual(response.status_code, 200)
        self.article.refresh_from_db()
        self.assertEqual(self.article.likes, initial_likes + 1)
