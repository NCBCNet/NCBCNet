"""
OKR评卷系统示例数据创建脚本

使用方法:
python manage.py shell < okr_exam/create_demo_data.py
"""

from django.contrib.auth.models import User
from okr_exam.models import ExamPaper, PaperSection, Question, QuestionOption

# 创建测试用户（如果不存在）
teacher, _ = User.objects.get_or_create(
    username='teacher',
    defaults={
        'is_staff': True,
        'is_superuser': False,
    }
)
teacher.set_password('teacher123')
teacher.save()

student, _ = User.objects.get_or_create(
    username='student',
    defaults={
        'is_staff': False,
        'is_superuser': False,
    }
)
student.set_password('student123')
student.save()

print("用户创建完成:")
print(f"  教师账号: teacher / teacher123")
print(f"  学生账号: student / student123")

# 创建示例试卷
paper = ExamPaper.objects.create(
    title='Python基础知识测试',
    description='本试卷测试Python编程基础知识，包括语法、数据类型、控制流等内容。',
    creator=teacher,
    total_score=100,
    duration=90,
    is_active=True
)

print(f"\n试卷创建完成: {paper.title}")

# 创建第一节：选择题部分
section1 = PaperSection.objects.create(
    paper=paper,
    title='第一部分：单项选择题',
    description='每题10分，共40分',
    order=1
)

# 添加选择题
q1 = Question.objects.create(
    section=section1,
    question_type='choice',
    content='Python是一种什么类型的编程语言？',
    score=10,
    order=1
)
QuestionOption.objects.create(question=q1, content='编译型语言', is_correct=False, order=1)
QuestionOption.objects.create(question=q1, content='解释型语言', is_correct=True, order=2)
QuestionOption.objects.create(question=q1, content='汇编语言', is_correct=False, order=3)
QuestionOption.objects.create(question=q1, content='机器语言', is_correct=False, order=4)

q2 = Question.objects.create(
    section=section1,
    question_type='choice',
    content='以下哪个不是Python的数据类型？',
    score=10,
    order=2
)
QuestionOption.objects.create(question=q2, content='int', is_correct=False, order=1)
QuestionOption.objects.create(question=q2, content='float', is_correct=False, order=2)
QuestionOption.objects.create(question=q2, content='char', is_correct=True, order=3)
QuestionOption.objects.create(question=q2, content='str', is_correct=False, order=4)

q3 = Question.objects.create(
    section=section1,
    question_type='choice',
    content='Python中如何定义一个函数？',
    score=10,
    order=3
)
QuestionOption.objects.create(question=q3, content='function myFunc():', is_correct=False, order=1)
QuestionOption.objects.create(question=q3, content='def myFunc():', is_correct=True, order=2)
QuestionOption.objects.create(question=q3, content='func myFunc():', is_correct=False, order=3)
QuestionOption.objects.create(question=q3, content='define myFunc():', is_correct=False, order=4)

q4 = Question.objects.create(
    section=section1,
    question_type='choice',
    content='以下哪个符号用于Python中的注释？',
    score=10,
    order=4
)
QuestionOption.objects.create(question=q4, content='//', is_correct=False, order=1)
QuestionOption.objects.create(question=q4, content='/* */', is_correct=False, order=2)
QuestionOption.objects.create(question=q4, content='#', is_correct=True, order=3)
QuestionOption.objects.create(question=q4, content='--', is_correct=False, order=4)

print(f"第一节创建完成: {section1.title} - 4道选择题")

# 创建第二节：多选题部分
section2 = PaperSection.objects.create(
    paper=paper,
    title='第二部分：多项选择题',
    description='每题10分，共20分',
    order=2
)

q5 = Question.objects.create(
    section=section2,
    question_type='multiple',
    content='以下哪些是Python的标准数据结构？（多选）',
    score=10,
    order=1
)
QuestionOption.objects.create(question=q5, content='list（列表）', is_correct=True, order=1)
QuestionOption.objects.create(question=q5, content='tuple（元组）', is_correct=True, order=2)
QuestionOption.objects.create(question=q5, content='dict（字典）', is_correct=True, order=3)
QuestionOption.objects.create(question=q5, content='array（数组）', is_correct=False, order=4)

q6 = Question.objects.create(
    section=section2,
    question_type='multiple',
    content='Python中哪些关键字用于异常处理？（多选）',
    score=10,
    order=2
)
QuestionOption.objects.create(question=q6, content='try', is_correct=True, order=1)
QuestionOption.objects.create(question=q6, content='except', is_correct=True, order=2)
QuestionOption.objects.create(question=q6, content='finally', is_correct=True, order=3)
QuestionOption.objects.create(question=q6, content='catch', is_correct=False, order=4)

print(f"第二节创建完成: {section2.title} - 2道多选题")

# 创建第三节：问答题部分
section3 = PaperSection.objects.create(
    paper=paper,
    title='第三部分：问答题',
    description='每题20分，共40分',
    order=3
)

q7 = Question.objects.create(
    section=section3,
    question_type='essay',
    content='请简述Python中列表（list）和元组（tuple）的区别。',
    score=20,
    order=1
)

q8 = Question.objects.create(
    section=section3,
    question_type='essay',
    content='请解释Python中的装饰器（decorator）是什么，并给出一个简单的使用示例。',
    score=20,
    order=2
)

print(f"第三节创建完成: {section3.title} - 2道问答题")

print("\n示例数据创建完成！")
print("\n下一步:")
print("1. 访问 http://localhost:8000/okr_exam/ 查看试卷列表")
print("2. 使用学生账号登录并参加考试")
print("3. 使用教师账号登录并进行评卷")
