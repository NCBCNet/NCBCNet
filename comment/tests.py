from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from article.models import Article
from .models import Comment


class CommentModelTest(TestCase):
    """测试Comment模型"""

    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.article = Article.objects.create(
            author=self.user,
            title='测试文章',
            content='测试内容',
            likes=0,
            total_views=0
        )
        self.comment = Comment.objects.create(
            article=self.article,
            user=self.user,
            content='这是一条测试评论'
        )

    def test_comment_creation(self):
        """测试评论创建"""
        self.assertTrue(isinstance(self.comment, Comment))
        self.assertEqual(self.comment.content, '这是一条测试评论')
        self.assertEqual(self.comment.user, self.user)
        self.assertEqual(self.comment.article, self.article)

    def test_comment_str(self):
        """测试评论字符串表示"""
        self.assertEqual(str(self.comment), self.comment.content[:20])

    def test_comment_article_relation(self):
        """测试评论与文章的关系"""
        self.assertIn(self.comment, self.article.comments.all())

    def test_comment_user_relation(self):
        """测试评论与用户的关系"""
        self.assertIn(self.comment, self.user.comments.all())


class CommentReplyTest(TestCase):
    """测试评论回复功能"""

    def setUp(self):
        """设置测试数据"""
        self.user1 = User.objects.create_user(
            username='user1',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='pass123'
        )
        self.article = Article.objects.create(
            author=self.user1,
            title='测试文章',
            content='内容',
            likes=0,
            total_views=0
        )
        self.parent_comment = Comment.objects.create(
            article=self.article,
            user=self.user1,
            content='父评论'
        )

    def test_reply_to_comment(self):
        """测试回复评论"""
        reply = Comment.objects.create(
            article=self.article,
            user=self.user2,
            content='回复内容',
            parent=self.parent_comment,
            reply_to=self.user1
        )
        self.assertEqual(reply.parent, self.parent_comment)
        self.assertEqual(reply.reply_to, self.user1)
        self.assertIn(reply, self.parent_comment.children.all())

    def test_nested_replies(self):
        """测试嵌套回复"""
        reply1 = Comment.objects.create(
            article=self.article,
            user=self.user2,
            content='一级回复',
            parent=self.parent_comment
        )
        reply2 = Comment.objects.create(
            article=self.article,
            user=self.user1,
            content='二级回复',
            parent=reply1
        )
        self.assertEqual(reply1.parent, self.parent_comment)
        self.assertEqual(reply2.parent, reply1)

    def test_comment_tree_structure(self):
        """测试评论树状结构"""
        # 创建多个回复
        reply1 = Comment.objects.create(
            article=self.article,
            user=self.user2,
            content='回复1',
            parent=self.parent_comment
        )
        reply2 = Comment.objects.create(
            article=self.article,
            user=self.user2,
            content='回复2',
            parent=self.parent_comment
        )

        # 检查父评论有多个子评论
        self.assertEqual(self.parent_comment.children.count(), 2)
        self.assertIn(reply1, self.parent_comment.children.all())
        self.assertIn(reply2, self.parent_comment.children.all())


class CommentViewTest(TestCase):
    """测试评论视图"""

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
            likes=0,
            total_views=0
        )

    def test_post_comment_not_logged_in(self):
        """测试未登录用户发表评论"""
        response = self.client.post(
            reverse('comment:post_comment', args=[self.article.id]),
            {'content': '测试评论'}
        )
        # 应该重定向到登录页面
        self.assertEqual(response.status_code, 302)

    def test_post_comment_logged_in(self):
        """测试已登录用户发表评论"""
        self.client.login(username='testuser', password='testpass123')
        initial_comment_count = Comment.objects.count()

        response = self.client.post(
            reverse('comment:post_comment', args=[self.article.id]),
            {'content': '这是一条新评论'}
        )

        # 检查评论是否创建
        self.assertEqual(Comment.objects.count(), initial_comment_count + 1)

        # 检查最新评论
        latest_comment = Comment.objects.latest('created')
        self.assertEqual(latest_comment.content, '这是一条新评论')
        self.assertEqual(latest_comment.user, self.user)
        self.assertEqual(latest_comment.article, self.article)


class CommentFilterTest(TestCase):
    """测试评论筛选功能"""

    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.article1 = Article.objects.create(
            author=self.user,
            title='文章1',
            content='内容1',
            likes=0,
            total_views=0
        )
        self.article2 = Article.objects.create(
            author=self.user,
            title='文章2',
            content='内容2',
            likes=0,
            total_views=0
        )
        self.comment1 = Comment.objects.create(
            article=self.article1,
            user=self.user,
            content='文章1的评论'
        )
        self.comment2 = Comment.objects.create(
            article=self.article2,
            user=self.user,
            content='文章2的评论'
        )

    def test_filter_comments_by_article(self):
        """测试按文章筛选评论"""
        article1_comments = Comment.objects.filter(article=self.article1)
        self.assertEqual(article1_comments.count(), 1)
        self.assertIn(self.comment1, article1_comments)
        self.assertNotIn(self.comment2, article1_comments)

    def test_filter_comments_by_user(self):
        """测试按用户筛选评论"""
        user_comments = Comment.objects.filter(user=self.user)
        self.assertEqual(user_comments.count(), 2)
        self.assertIn(self.comment1, user_comments)
        self.assertIn(self.comment2, user_comments)
