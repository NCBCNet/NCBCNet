from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import ExamPaper, PaperSection, Question, QuestionOption, ExamSubmission, Answer


def exam_list(request):
    """试卷列表"""
    papers = ExamPaper.objects.filter(is_active=True)
    return render(request, 'okr_exam/exam_list.html', {'papers': papers})


@login_required
def exam_detail(request, paper_id):
    """试卷详情"""
    paper = get_object_or_404(ExamPaper, id=paper_id, is_active=True)
    sections = paper.sections.prefetch_related('questions__options').all()
    
    # 检查是否已有提交记录
    submission = ExamSubmission.objects.filter(
        paper=paper,
        student=request.user,
        is_submitted=False
    ).first()
    
    return render(request, 'okr_exam/exam_detail.html', {
        'paper': paper,
        'sections': sections,
        'submission': submission
    })


@login_required
def start_exam(request, paper_id):
    """开始考试"""
    paper = get_object_or_404(ExamPaper, id=paper_id, is_active=True)
    
    # 检查是否已有未提交的提交记录
    submission = ExamSubmission.objects.filter(
        paper=paper,
        student=request.user,
        is_submitted=False
    ).first()
    
    if not submission:
        submission = ExamSubmission.objects.create(
            paper=paper,
            student=request.user,
            total_score=paper.total_score
        )
    
    return redirect('okr_exam:take_exam', submission_id=submission.id)


@login_required
def take_exam(request, submission_id):
    """考试界面"""
    submission = get_object_or_404(
        ExamSubmission,
        id=submission_id,
        student=request.user,
        is_submitted=False
    )
    
    paper = submission.paper
    sections = paper.sections.prefetch_related('questions__options').all()
    
    if request.method == 'POST':
        # 保存答案
        for section in sections:
            for question in section.questions.all():
                answer, created = Answer.objects.get_or_create(
                    submission=submission,
                    question=question
                )
                
                if question.question_type in ['choice', 'multiple']:
                    option_ids = request.POST.getlist(f'question_{question.id}')
                    answer.selected_options.set(QuestionOption.objects.filter(id__in=option_ids))
                    
                    # 自动评分选择题
                    answer.score = 0  # Reset score first
                    if question.question_type == 'choice':
                        if option_ids and len(option_ids) == 1:
                            try:
                                selected_option = QuestionOption.objects.get(id=option_ids[0])
                                if selected_option.is_correct:
                                    answer.score = question.score
                            except QuestionOption.DoesNotExist:
                                pass  # Invalid option, score remains 0
                        answer.is_graded = True
                    elif question.question_type == 'multiple':
                        correct_options = set(question.options.filter(is_correct=True).values_list('id', flat=True))
                        try:
                            selected_set = set(int(id) for id in option_ids)
                            if correct_options == selected_set:
                                answer.score = question.score
                        except (ValueError, TypeError):
                            pass  # Invalid option ID, score remains 0
                        answer.is_graded = True
                else:
                    answer.content = request.POST.get(f'question_{question.id}', '')
                
                answer.save()
        
        # 提交试卷
        if 'submit' in request.POST:
            submission.is_submitted = True
            submission.submitted_at = timezone.now()
            
            # 计算已评分的得分
            graded_score = sum(
                answer.score for answer in submission.answers.filter(is_graded=True)
            )
            submission.graded_score = graded_score
            
            # 如果所有题目都已评分，标记为已评分
            total_answers = submission.answers.count()
            graded_answers = submission.answers.filter(is_graded=True).count()
            if total_answers == graded_answers:
                submission.is_graded = True
                submission.graded_at = timezone.now()
            
            submission.save()
            messages.success(request, '试卷提交成功！')
            return redirect('okr_exam:submission_detail', submission_id=submission.id)
        
        messages.success(request, '答案已保存！')
    
    return render(request, 'okr_exam/take_exam.html', {
        'submission': submission,
        'paper': paper,
        'sections': sections
    })


@login_required
def submission_detail(request, submission_id):
    """提交详情"""
    submission = get_object_or_404(ExamSubmission, id=submission_id)
    
    # 学生只能查看自己的提交
    if submission.student != request.user and not request.user.is_staff:
        messages.error(request, '您没有权限查看此提交。')
        return redirect('okr_exam:exam_list')
    
    answers = submission.answers.select_related('question', 'question__section').prefetch_related('selected_options').all()
    
    # 按分节组织答案
    sections_data = {}
    for answer in answers:
        section = answer.question.section
        if section.id not in sections_data:
            sections_data[section.id] = {
                'section': section,
                'answers': []
            }
        sections_data[section.id]['answers'].append(answer)
    
    return render(request, 'okr_exam/submission_detail.html', {
        'submission': submission,
        'sections_data': sections_data.values()
    })


@login_required
def grading_list(request):
    """评卷列表 - 仅教师可访问"""
    if not request.user.is_staff:
        messages.error(request, '您没有权限访问此页面。')
        return redirect('okr_exam:exam_list')
    
    submissions = ExamSubmission.objects.filter(
        is_submitted=True
    ).select_related('paper', 'student', 'grader').order_by('-submitted_at')
    
    # 筛选
    paper_id = request.GET.get('paper')
    is_graded = request.GET.get('is_graded')
    
    if paper_id:
        submissions = submissions.filter(paper_id=paper_id)
    if is_graded:
        submissions = submissions.filter(is_graded=(is_graded == 'true'))
    
    papers = ExamPaper.objects.filter(is_active=True)
    
    return render(request, 'okr_exam/grading_list.html', {
        'submissions': submissions,
        'papers': papers
    })


@login_required
def grade_submission(request, submission_id):
    """评卷"""
    if not request.user.is_staff:
        messages.error(request, '您没有权限访问此页面。')
        return redirect('okr_exam:exam_list')
    
    submission = get_object_or_404(ExamSubmission, id=submission_id, is_submitted=True)
    answers = submission.answers.select_related('question', 'question__section').prefetch_related('selected_options').all()
    
    if request.method == 'POST':
        # 保存评分
        for answer in answers:
            if not answer.is_graded:
                score = request.POST.get(f'score_{answer.id}', '0')
                feedback = request.POST.get(f'feedback_{answer.id}', '')
                
                try:
                    answer.score = float(score)
                    answer.feedback = feedback
                    answer.is_graded = True
                    answer.save()
                except ValueError:
                    messages.error(request, f'题目"{answer.question.content[:30]}"的分数格式不正确。')
                    return redirect('okr_exam:grade_submission', submission_id=submission_id)
        
        # 更新提交记录
        total_score = sum(answer.score for answer in submission.answers.all())
        submission.graded_score = total_score
        submission.is_graded = True
        submission.grader = request.user
        submission.graded_at = timezone.now()
        submission.save()
        
        messages.success(request, '评卷完成！')
        return redirect('okr_exam:grading_list')
    
    # 按分节组织答案
    sections_data = {}
    for answer in answers:
        section = answer.question.section
        if section.id not in sections_data:
            sections_data[section.id] = {
                'section': section,
                'answers': []
            }
        sections_data[section.id]['answers'].append(answer)
    
    return render(request, 'okr_exam/grade_submission.html', {
        'submission': submission,
        'sections_data': sections_data.values()
    })


@login_required
def my_submissions(request):
    """我的提交记录"""
    submissions = ExamSubmission.objects.filter(
        student=request.user,
        is_submitted=True
    ).select_related('paper').order_by('-submitted_at')
    
    return render(request, 'okr_exam/my_submissions.html', {
        'submissions': submissions
    })
