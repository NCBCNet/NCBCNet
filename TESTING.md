# Django网站测试文档 / Django Website Testing Documentation

## 概述 / Overview

本项目包含了完整的Django网站测试样本，覆盖了以下应用的功能测试：
This project contains comprehensive Django website test samples covering functional tests for the following apps:

- **Article (文章)**: 文章模型和视图测试
- **Comment (评论)**: 评论系统和MPTT树状结构测试
- **Usermanage (用户管理)**: 用户注册、登录、资料管理测试
- **Server (服务器)**: 主页和基础视图测试
- **Study (学习)**: 学习应用基础测试
- **FileSave (文件保存)**: 文件处理基础测试

## 测试统计 / Test Statistics

- **总测试数 / Total Tests**: 64
- **测试通过率 / Pass Rate**: 100%
- **覆盖的应用 / Apps Covered**: 6

## 运行测试 / Running Tests

### 准备工作 / Prerequisites

1. 安装项目依赖 / Install project dependencies:
```bash
pip install -r requirements.txt
```

2. 创建SECRET文件用于测试 / Create SECRET file for testing:
```bash
echo "django-insecure-test-key" > SECRET
```

### 运行所有测试 / Run All Tests

使用测试配置运行所有测试：
Run all tests using test settings:

```bash
python manage.py test --settings=NCBCNet.test_settings
```

### 运行特定应用的测试 / Run Tests for Specific Apps

运行文章应用测试 / Run article app tests:
```bash
python manage.py test article --settings=NCBCNet.test_settings
```

运行评论应用测试 / Run comment app tests:
```bash
python manage.py test comment --settings=NCBCNet.test_settings
```

运行用户管理应用测试 / Run usermanage app tests:
```bash
python manage.py test usermanage --settings=NCBCNet.test_settings
```

运行服务器应用测试 / Run server app tests:
```bash
python manage.py test server --settings=NCBCNet.test_settings
```

### 详细输出模式 / Verbose Output Mode

使用 `-v 2` 参数查看详细的测试输出：
Use `-v 2` for detailed test output:

```bash
python manage.py test --settings=NCBCNet.test_settings -v 2
```

## 测试配置 / Test Configuration

### test_settings.py

项目包含专门的测试配置文件 `NCBCNet/test_settings.py`，该文件：
The project includes a dedicated test configuration file that:

- 使用SQLite内存数据库 (Use SQLite in-memory database)
- 禁用SSL和安全设置 (Disable SSL and security settings)
- 使用快速密码哈希器 (Use fast password hashers)
- 禁用迁移以加快测试速度 (Disable migrations for faster tests)

## 测试内容 / Test Coverage

### Article应用测试 / Article App Tests

**模型测试 (Model Tests)**:
- ArticleColumn创建和字段测试
- Article创建、内容和关系测试
- 文章排序测试
- URL生成测试

**视图测试 (View Tests)**:
- 文章列表视图
- 文章详情视图（包括浏览次数增加）
- 文章创建（需要登录）
- 文章更新（仅作者）
- 文章删除（仅作者）
- 按浏览量排序
- 按专栏筛选

**点赞功能测试 (Like Feature Tests)**:
- 增加点赞数测试

### Comment应用测试 / Comment App Tests

**模型测试 (Model Tests)**:
- Comment创建和基本字段
- 评论与文章、用户的关系
- 评论字符串表示

**回复功能测试 (Reply Feature Tests)**:
- 回复评论
- 嵌套回复
- MPTT树状结构

**视图测试 (View Tests)**:
- 发表评论（需要登录）
- 评论列表显示

**筛选测试 (Filter Tests)**:
- 按文章筛选评论
- 按用户筛选评论

### Usermanage应用测试 / Usermanage App Tests

**Profile模型测试 (Profile Model Tests)**:
- Profile创建
- 字段验证
- 与User的一对一关系

**注册测试 (Registration Tests)**:
- 访问注册页面
- 注册新用户
- 重复用户名处理

**登录测试 (Login Tests)**:
- 访问登录页面
- 有效凭证登录
- 无效凭证处理
- 不存在的用户处理

**登出测试 (Logout Tests)**:
- 用户登出功能

**资料编辑测试 (Profile Edit Tests)**:
- 访问编辑页面
- 自动创建Profile
- 更新用户资料
- 权限验证（不能编辑他人资料）

**账号删除测试 (Account Deletion Tests)**:
- 删除自己的账号
- 不能删除他人账号
- 未登录限制

### Server应用测试 / Server App Tests

**视图测试 (View Tests)**:
- 首页访问
- 关于页面
- 彩蛋页面

**URL测试 (URL Tests)**:
- URL解析正确性

**响应测试 (Response Tests)**:
- HTML内容类型
- 404页面处理
- 多次加载稳定性

### Study和FileSave应用测试 / Study & FileSave App Tests

**基础测试 (Basic Tests)**:
- 应用安装验证
- 应用配置验证
- 文件处理功能基础测试

## 测试最佳实践 / Testing Best Practices

1. **运行测试前 / Before Running Tests**:
   - 确保所有依赖已安装
   - 使用测试配置文件
   - 不需要运行迁移

2. **编写新测试 / Writing New Tests**:
   - 继承 `django.test.TestCase`
   - 在 `setUp()` 方法中准备测试数据
   - 使用有意义的测试方法名
   - 添加中文文档字符串说明测试目的

3. **测试命名规范 / Test Naming Convention**:
   - 测试方法以 `test_` 开头
   - 使用描述性名称，如 `test_user_can_login`
   - 测试类以 `Test` 结尾

## 故障排除 / Troubleshooting

### 问题: ModuleNotFoundError

解决方案 / Solution:
```bash
pip install -r requirements.txt
```

### 问题: SECRET文件不存在

解决方案 / Solution:
```bash
echo "django-insecure-test-key-for-testing" > SECRET
```

### 问题: 数据库错误

解决方案 / Solution:
使用测试配置文件，它会使用内存数据库：
Use test settings which uses in-memory database:
```bash
python manage.py test --settings=NCBCNet.test_settings
```

## 持续集成 / Continuous Integration

这些测试可以集成到CI/CD流程中：
These tests can be integrated into CI/CD pipelines:

```yaml
# GitHub Actions示例 / GitHub Actions example
- name: Run tests
  run: |
    pip install -r requirements.txt
    echo "test-secret-key" > SECRET
    python manage.py test --settings=NCBCNet.test_settings
```

## 贡献指南 / Contributing

添加新测试时，请确保：
When adding new tests, please ensure:

1. 测试通过 / Tests pass
2. 遵循现有的测试结构 / Follow existing test structure
3. 包含中英文文档 / Include Chinese and English documentation
4. 测试覆盖关键功能 / Cover critical functionality

## 许可证 / License

与主项目保持一致 / Same as the main project
