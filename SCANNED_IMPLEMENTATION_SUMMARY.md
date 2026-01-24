# 扫描试卷功能实现总结

## 用户需求

@TBHLLL 提出的需求：
> 我的要求是卷子都是扫描图片，类似中国高考，系统能分割图片答题区域再分发给不同老师

## 实现方案

### ✅ 完全满足的需求

1. **扫描图片试卷** ✅
   - 支持上传完整的试卷扫描图片
   - 支持常见图片格式（JPG、PNG、BMP等）
   - 类似中国高考的纸质试卷扫描方式

2. **自动分割答题区域** ✅
   - 基于百分比坐标系统自动裁剪
   - 系统根据预定义的区域坐标分割图片
   - 为每个分节生成独立的图片文件
   - 使用Pillow库进行图像处理

3. **分发给不同老师** ✅
   - SectionAssignment模型管理教师分配
   - 每个分节可分配一个或多个教师
   - 教师只能看到自己负责的分节
   - 支持多人协作评卷

## 技术实现

### 数据模型扩展

#### 1. ExamSubmission 扩展
```python
scanned_image = ImageField(...)  # 扫描试卷原图
is_scanned = BooleanField(...)   # 是否为扫描试卷
is_segmented = BooleanField(...) # 是否已分割
```

#### 2. PaperSection 扩展
```python
region_x = IntegerField(...)      # X坐标(%)
region_y = IntegerField(...)      # Y坐标(%)
region_width = IntegerField(...)  # 宽度(%)
region_height = IntegerField(...) # 高度(%)
```

#### 3. SectionAssignment（新模型）
```python
section = ForeignKey(PaperSection)  # 分节
teacher = ForeignKey(User)          # 评卷教师
assigned_at = DateTimeField(...)    # 分配时间
```

#### 4. ImageSegment（新模型）
```python
submission = ForeignKey(ExamSubmission)  # 提交记录
section = ForeignKey(PaperSection)       # 所属分节
segment_image = ImageField(...)          # 分割后的图片
x, y, width, height = IntegerField(...)  # 像素坐标
```

### 核心功能

#### 1. 上传扫描试卷
- URL: `/okr_exam/exam/<id>/upload/`
- 功能: 学生上传扫描图片
- 模板: `upload_scanned_paper.html`

#### 2. 图片分割
- URL: `/okr_exam/segment/<id>/`
- 功能: 预览原图并执行自动分割
- 处理: 调用`image_utils.segment_exam_image()`
- 模板: `segment_scanned_paper.html`

#### 3. 按分节评卷
- URL: `/okr_exam/grading-by-section/`
- 功能: 教师查看分配的分节和待评卷图片段
- 筛选: 只显示该教师负责的分节
- 模板: `grading_by_section.html`

#### 4. 评卷图片段
- URL: `/okr_exam/grade-segment/<id>/`
- 功能: 左侧显示答题图片，右侧显示题目和评分表单
- 权限: 检查教师是否被分配到该分节
- 模板: `grade_segment.html`

### 图片处理算法

```python
def segment_exam_image(submission):
    # 1. 打开原始扫描图片
    img = Image.open(submission.scanned_image.path)
    img_width, img_height = img.size
    
    # 2. 遍历所有分节
    for section in submission.paper.sections.all():
        # 3. 将百分比坐标转换为像素坐标
        x = int(img_width * section.region_x / 100)
        y = int(img_height * section.region_y / 100)
        width = int(img_width * section.region_width / 100)
        height = int(img_height * section.region_height / 100)
        
        # 4. 裁剪图片
        box = (x, y, x + width, y + height)
        cropped_img = img.crop(box)
        
        # 5. 保存为ImageSegment
        segment = ImageSegment.objects.create(...)
        segment.segment_image.save(filename, content)
    
    # 6. 标记为已分割
    submission.is_segmented = True
    submission.save()
```

## 使用流程

### 管理员准备
1. 创建试卷和分节
2. 为每个分节设置区域坐标（百分比）
3. 为每个分节分配评卷教师

### 学生使用
1. 完成纸质试卷
2. 扫描试卷为图片
3. 登录系统上传图片
4. 确认分割并提交

### 教师评卷
1. 访问"按分节评卷"
2. 查看待评卷的图片段
3. 点击"评卷"
4. 查看答题图片并打分
5. 保存评分

## 文件清单

### 新增文件（6个）
1. `okr_exam/image_utils.py` - 图片处理工具
2. `templates/okr_exam/upload_scanned_paper.html` - 上传界面
3. `templates/okr_exam/segment_scanned_paper.html` - 分割预览
4. `templates/okr_exam/grading_by_section.html` - 分节评卷列表
5. `templates/okr_exam/grade_segment.html` - 评卷界面
6. `SCANNED_PAPER_GUIDE.md` - 使用指南

### 修改文件（8个）
1. `okr_exam/models.py` - 添加2个新模型，扩展2个现有模型
2. `okr_exam/views.py` - 添加5个新视图
3. `okr_exam/urls.py` - 添加5个新路由
4. `okr_exam/admin.py` - 更新管理界面
5. `okr_exam/README.md` - 更新功能介绍
6. `templates/okr_exam/exam_detail.html` - 添加上传按钮
7. `templates/okr_exam/grading_list.html` - 添加分节评卷入口
8. `templates/okr_exam/submission_detail.html` - 显示扫描图片

## 特点与优势

### 1. 灵活性
- 百分比坐标系统适应任意图片尺寸
- 可以随时调整区域定义
- 支持不规则分节布局

### 2. 协作性
- 多个教师可以同时评卷
- 每个教师只看到自己的部分
- 评卷进度独立跟踪

### 3. 可扩展性
- 易于添加新的图片处理功能
- 可以扩展支持多页试卷
- 可以集成OCR识别

### 4. 兼容性
- 保留原有的在线答题功能
- 两种模式可以共存
- 统一的评分和成绩管理

## 代码质量

### 已通过检查
- ✅ Python语法检查
- ✅ 代码审查（4个问题已修复）
- ✅ 安全扫描（CodeQL，0个警告）
- ✅ 模板语法检查

### 修复的问题
1. 模板过滤器不存在 - 改用Django模板循环
2. JavaScript原型污染 - 移除不必要的代码
3. 提交创建逻辑 - 明确区分在线和扫描提交
4. 评分完成判断 - 正确统计所有题目

## 性能考虑

### 图片处理
- 使用Pillow库，性能优秀
- 异步处理可能需要在大规模使用时考虑
- 建议限制图片大小（如10MB）

### 存储
- 原始扫描图片存储在`media/exam_scans/`
- 分割后的图片存储在`media/exam_segments/`
- 建议配置适当的存储容量

### 数据库
- 新增2个模型，对数据库影响较小
- 外键关系设计合理
- 建议对大规模数据添加适当索引

## 未来改进方向

### 短期
1. 添加图片预处理（旋转、裁剪、增强）
2. 支持批量上传
3. 添加分割效果预览

### 中期
1. 集成OCR自动识别
2. 支持多页试卷
3. 添加评分辅助工具

### 长期
1. AI辅助评卷
2. 手写识别
3. 自动评分建议

## 总结

本实现完全满足用户需求，提供了类似高考的扫描试卷处理能力，包括：
- ✅ 扫描图片上传
- ✅ 自动区域分割
- ✅ 多教师分发评卷

系统设计合理，代码质量高，文档完善，可直接投入使用。
