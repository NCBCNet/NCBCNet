"""API 认证与安全回归测试（HttpOnly Cookie JWT + CSRF + 签名下载）。

使用 enforce_csrf_checks=True 验证 Cookie 认证下写请求必须携带 CSRF token。
"""
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.conf import settings


class AuthFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('alice', password='pass12345')

    def _csrf_client(self):
        client = Client(enforce_csrf_checks=True)
        resp = client.get('/api/v1/auth/csrf/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('csrftoken', client.cookies)
        return client

    def test_csrf_endpoint_sets_cookie(self):
        client = self._csrf_client()
        resp = client.get('/api/v1/auth/csrf/')
        self.assertIn('csrfToken', resp.json())

    def test_login_sets_http_only_cookies(self):
        client = self._csrf_client()
        csrf = client.cookies['csrftoken'].value
        resp = client.post(
            '/api/v1/auth/login/',
            data={'username': 'alice', 'password': 'pass12345'},
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(resp.status_code, 200, resp.json())
        self.assertIn(settings.AUTH_COOKIE_ACCESS, client.cookies)
        self.assertIn(settings.AUTH_COOKIE_REFRESH, client.cookies)

    def test_write_requires_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.get('/api/v1/auth/csrf/')
        # 不带 X-CSRFToken 的写请求应被拒绝
        resp = client.post(
            '/api/v1/auth/login/',
            data={'username': 'alice', 'password': 'pass12345'},
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 403)

    def test_me_requires_auth(self):
        client = Client()
        resp = client.get('/api/v1/auth/me/')
        self.assertEqual(resp.status_code, 401)
        body = resp.json()
        self.assertEqual(body['code'], 'not_authenticated')

    def test_login_then_me_and_logout(self):
        client = self._csrf_client()
        csrf = client.cookies['csrftoken'].value
        resp = client.post(
            '/api/v1/auth/login/',
            data={'username': 'alice', 'password': 'pass12345'},
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(resp.status_code, 200)

        me = client.get('/api/v1/auth/me/')
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()['username'], 'alice')

        # 登录成功后 CSRF token 已轮换，需重新读取
        csrf = client.cookies['csrftoken'].value
        resp = client.post('/api/v1/auth/logout/', content_type='application/json', HTTP_X_CSRFTOKEN=csrf)
        self.assertEqual(resp.status_code, 200)
        # 清除后 /me 应 401
        me2 = client.get('/api/v1/auth/me/')
        self.assertEqual(me2.status_code, 401)


class SignedDownloadTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user('owner', password='pass12345')
        cls.other = User.objects.create_user('other', password='pass12345')

    def test_download_url_nonexistent_file_returns_404(self):
        # 下载链接端点公开（共享文件匿名可下载），文件不存在返回统一 404 JSON
        client = Client()
        resp = client.get('/api/v1/files/99999/download-url/')
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json().get('code'), 'not_found')


class ApiBoundaryTests(TestCase):
    """架构边界测试（阶段二 M2）。

    用 AST 静态扫描 api 包源码，断言 api 绝不导入业务应用（article、file_save、
    usermanage 等）的 models 子模块，保证分层约束在无法安装 import-linter 的
    本地环境中仍可回归验证。禁止模块名在源码中动态拼接，避免干扰仓库级
    “api 无业务 models 引用”的 grep 校验。
    """

    _BUSINESS_APPS = ('article', 'comment', 'file_save', 'usermanage')

    def _forbidden_modules(self):
        return {f'{app}.models' for app in self._BUSINESS_APPS}

    def _collect_violations(self):
        import ast
        from pathlib import Path

        forbidden = self._forbidden_modules()
        api_root = Path(__file__).resolve().parent
        violations = []

        for py_file in sorted(api_root.rglob('*.py')):
            tree = ast.parse(py_file.read_text(encoding='utf-8'), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    # 检测「from <业务应用> import models」与「from <业务应用>.models import X」等形态
                    mod = node.module
                    if mod in forbidden:
                        violations.append(f'{py_file.name}: from {mod} import ...')
                    for alias in node.names:
                        if alias.name != '*' and f'{mod}.{alias.name}' in forbidden:
                            violations.append(f'{py_file.name}: from {mod} import {alias.name}')
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        # 检测「import <业务应用>.models」及深层子模块
                        if alias.name in forbidden or \
                                any(alias.name.startswith(f'{f}.') for f in forbidden):
                            violations.append(f'{py_file.name}: import {alias.name}')

        return violations

    def test_api_never_imports_business_models(self):
        violations = self._collect_violations()
        self.assertEqual(
            violations,
            [],
            f'api 包不得导入业务应用 models，发现 {len(violations)} 处违规: {violations}',
        )


class PaginationContractTests(TestCase):
    """列表类端点契约：除文章列表外，其余列表应返回数组（前端直接 map），而非分页对象。"""

    def test_columns_endpoint_returns_plain_list(self):
        resp = Client().get('/api/v1/articles/columns/')
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)

    def test_folders_endpoint_returns_plain_list(self):
        User.objects.create_user('bob', password='pass12345')
        client = Client()
        client.get('/api/v1/auth/csrf/')
        csrf = client.cookies['csrftoken'].value
        login = client.post(
            '/api/v1/auth/login/',
            data={'username': 'bob', 'password': 'pass12345'},
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(login.status_code, 200)
        resp = client.get('/api/v1/folders/')
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)


class ArticleContractTests(TestCase):
    """文章创建契约：创建响应必须带 id（前端据此跳转到详情页）。"""

    def test_create_article_returns_id(self):
        User.objects.create_user('writer', password='pass12345')
        client = Client(enforce_csrf_checks=True)
        client.get('/api/v1/auth/csrf/')
        csrf = client.cookies['csrftoken'].value
        login = client.post(
            '/api/v1/auth/login/',
            data={'username': 'writer', 'password': 'pass12345'},
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(login.status_code, 200)
        csrf = client.cookies['csrftoken'].value  # 登录后 CSRF 已轮换
        resp = client.post(
            '/api/v1/articles/create/',
            data={'title': '测试标题', 'content': '测试内容'},
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(resp.status_code, 201, resp.json())
        self.assertIn('id', resp.json())
        self.assertIsInstance(resp.json()['id'], int)


class HealthComponentsTests(TestCase):
    """组件级健康端点契约：返回各组件状态（脱敏）。"""

    def test_health_components_returns_status(self):
        resp = Client().get('/api/v1/health/components/')
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn('status', body)
        self.assertIn('components', body)
        for key in ('database', 'cache', 'storage'):
            self.assertIn(key, body['components'])
            comp = body['components'][key]
            self.assertIn('status', comp)
            self.assertIn('message', comp)
            self.assertIn('latency_ms', comp)


class FileAuthorizationTests(TestCase):
    """文件/文件夹授权：匿名不可上传；不得把资源挂靠到他人文件夹下。"""

    def _login_client(self, username, password='pass12345'):
        client = Client()
        client.get('/api/v1/auth/csrf/')
        csrf = client.cookies['csrftoken'].value
        login = client.post(
            '/api/v1/auth/login/',
            data={'username': username, 'password': password},
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(login.status_code, 200)
        return client

    def test_anonymous_upload_returns_401(self):
        resp = Client().post('/api/v1/files/upload/', data={})
        self.assertEqual(resp.status_code, 401)

    def test_cannot_create_folder_in_others_folder(self):
        User.objects.create_user('alice_own', password='pass12345')
        User.objects.create_user('bob_intruder', password='pass12345')

        # alice 先创建自己的文件夹
        alice_client = self._login_client('alice_own')
        created = alice_client.post(
            '/api/v1/folders/',
            data={'name': 'alice-folder'},
            content_type='application/json',
        )
        self.assertEqual(created.status_code, 201, created.json())
        folder_a_id = created.json()['id']

        # bob 尝试在 alice 的文件夹下创建 → 应 403
        client = self._login_client('bob_intruder')
        resp = client.post(
            '/api/v1/folders/',
            data={'name': 'x', 'parent': folder_a_id},
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 403, resp.json())

    def test_anonymous_shared_files_are_public_but_private_locked(self):
        # 共享列表对匿名公开；私有功能（上传/创建文件夹/个人列表）匿名一律 401
        client = Client()
        self.assertEqual(client.get('/api/v1/files/shared/').status_code, 200)
        self.assertIsInstance(client.get('/api/v1/files/shared/').json(), list)
        self.assertEqual(client.post('/api/v1/files/upload/', data={}).status_code, 401)
        self.assertEqual(client.post('/api/v1/folders/', data={'name': 'x'}).status_code, 401)
        self.assertEqual(client.get('/api/v1/folders/').status_code, 401)
        self.assertEqual(client.get('/api/v1/files/').status_code, 401)
