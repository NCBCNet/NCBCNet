from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class ExamPaper(models.Model):
    """试卷模型"""
    title = models.CharField(max_length=200, verbose_name='试卷标题')
    description = models.TextField(blank=True, verbose_name='试卷描述')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_papers', verbose_name='创建者')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    total_score = models.IntegerField(default=100, verbose_name='总分')
    duration = models.IntegerField(default=120, verbose_name='考试时长(分钟)')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    
    class Meta:
        verbose_name = '试卷'
        verbose_name_plural = '试卷'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class PaperSection(models.Model):
    """试卷分节模型 - 用于分割试卷"""
    paper = models.ForeignKey(ExamPaper, on_delete=models.CASCADE, related_name='sections', verbose_name='所属试卷')
    title = models.CharField(max_length=200, verbose_name='分节标题')
    description = models.TextField(blank=True, verbose_name='分节说明')
    order = models.IntegerField(default=0, verbose_name='排序')
    
    class Meta:
        verbose_name = '试卷分节'
        verbose_name_plural = '试卷分节'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.paper.title} - {self.title}"


class Question(models.Model):
    """题目模型"""
    QUESTION_TYPES = [
        ('choice', '选择题'),
        ('multiple', '多选题'),
        ('essay', '问答题'),
        ('fill', '填空题'),
    ]
    
    section = models.ForeignKey(PaperSection, on_delete=models.CASCADE, related_name='questions', verbose_name='所属分节')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='choice', verbose_name='题目类型')
    content = models.TextField(verbose_name='题目内容')
    score = models.IntegerField(default=10, verbose_name='分值')
    order = models.IntegerField(default=0, verbose_name='排序')
    
    class Meta:
        verbose_name = '题目'
        verbose_name_plural = '题目'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.section.paper.title} - {self.content[:30]}"


class QuestionOption(models.Model):
    """选择题选项模型"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options', verbose_name='所属题目')
    content = models.CharField(max_length=500, verbose_name='选项内容')
    is_correct = models.BooleanField(default=False, verbose_name='是否正确答案')
    order = models.IntegerField(default=0, verbose_name='排序')
    
    class Meta:
        verbose_name = '题目选项'
        verbose_name_plural = '题目选项'
        ordering = ['order']
    
    def __str__(self):
        return self.content


class ExamSubmission(models.Model):
    """考试提交记录"""
    paper = models.ForeignKey(ExamPaper, on_delete=models.CASCADE, related_name='submissions', verbose_name='试卷')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exam_submissions', verbose_name='学生')
    started_at = models.DateTimeField(default=timezone.now, verbose_name='开始时间')
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name='提交时间')
    is_submitted = models.BooleanField(default=False, verbose_name='是否已提交')
    total_score = models.FloatField(default=0, verbose_name='总分')
    graded_score = models.FloatField(default=0, verbose_name='得分')
    is_graded = models.BooleanField(default=False, verbose_name='是否已评分')
    grader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_submissions', verbose_name='评卷人')
    graded_at = models.DateTimeField(null=True, blank=True, verbose_name='评卷时间')
    
    class Meta:
        verbose_name = '考试提交'
        verbose_name_plural = '考试提交'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.paper.title}"


class Answer(models.Model):
    """答案模型"""
    submission = models.ForeignKey(ExamSubmission, on_delete=models.CASCADE, related_name='answers', verbose_name='提交记录')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name='题目')
    content = models.TextField(blank=True, verbose_name='答案内容')
    selected_options = models.ManyToManyField(QuestionOption, blank=True, verbose_name='选中的选项')
    score = models.FloatField(default=0, verbose_name='得分')
    is_graded = models.BooleanField(default=False, verbose_name='是否已评分')
    feedback = models.TextField(blank=True, verbose_name='评语')
    
    class Meta:
        verbose_name = '答案'
        verbose_name_plural = '答案'
    
    def __str__(self):
        return f"{self.submission.student.username} - {self.question.content[:30]}"
