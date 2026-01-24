from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count, Sum
from django.db import models
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


@login_required
def upload_scanned_paper(request, paper_id):
    """上传扫描试卷图片"""
    paper = get_object_or_404(ExamPaper, id=paper_id, is_active=True)
    
    if request.method == 'POST' and request.FILES.get('scanned_image'):
        # 查找或创建扫描试卷提交记录
        submission = ExamSubmission.objects.filter(
            paper=paper,
            student=request.user,
            is_submitted=False,
            is_scanned=True
        ).first()
        
        if not submission:
            submission = ExamSubmission.objects.create(
                paper=paper,
                student=request.user,
                total_score=paper.total_score,
                is_scanned=True
            )
        
        # 保存扫描图片
        submission.scanned_image = request.FILES['scanned_image']
        submission.save()
        
        messages.success(request, '扫描试卷上传成功！')
        return redirect('okr_exam:segment_scanned_paper', submission_id=submission.id)
    
    return render(request, 'okr_exam/upload_scanned_paper.html', {
        'paper': paper
    })


@login_required
def segment_scanned_paper(request, submission_id):
    """分割扫描试卷图片"""
    submission = get_object_or_404(
        ExamSubmission,
        id=submission_id,
        student=request.user
    )
    
    if not submission.is_scanned or not submission.scanned_image:
        messages.error(request, '该提交没有扫描图片')
        return redirect('okr_exam:exam_list')
    
    if request.method == 'POST':
        from .image_utils import segment_exam_image
        
        try:
            # 执行图片分割
            segments = segment_exam_image(submission)
            
            # 标记为已提交
            submission.is_submitted = True
            submission.submitted_at = timezone.now()
            submission.save()
            
            messages.success(request, f'试卷分割完成！共分割了 {len(segments)} 个区域')
            return redirect('okr_exam:submission_detail', submission_id=submission.id)
        except Exception as e:
            messages.error(request, f'分割失败: {str(e)}')
    
    return render(request, 'okr_exam/segment_scanned_paper.html', {
        'submission': submission
    })


@login_required
def grading_by_section(request):
    """按分节查看待评卷提交（教师）"""
    if not request.user.is_staff:
        messages.error(request, '您没有权限访问此页面。')
        return redirect('okr_exam:exam_list')
    
    from .models import SectionAssignment, ImageSegment
    
    # 获取该教师负责的分节
    assigned_sections = SectionAssignment.objects.filter(
        teacher=request.user
    ).select_related('section', 'section__paper')
    
    # 获取这些分节的待评卷图片段
    section_ids = [a.section.id for a in assigned_sections]
    segments = ImageSegment.objects.filter(
        section_id__in=section_ids,
        submission__is_submitted=True
    ).select_related('submission', 'section', 'submission__student').order_by('-created_at')
    
    return render(request, 'okr_exam/grading_by_section.html', {
        'assigned_sections': assigned_sections,
        'segments': segments
    })


@login_required
def grade_segment(request, segment_id):
    """评卷图片段"""
    if not request.user.is_staff:
        messages.error(request, '您没有权限访问此页面。')
        return redirect('okr_exam:exam_list')
    
    from .models import ImageSegment, SectionAssignment
    
    segment = get_object_or_404(ImageSegment, id=segment_id)
    
    # 检查教师是否被分配到该分节
    if not SectionAssignment.objects.filter(section=segment.section, teacher=request.user).exists():
        messages.error(request, '您没有权限评阅该分节。')
        return redirect('okr_exam:grading_by_section')
    
    # 获取该分节的所有题目
    questions = segment.section.questions.all()
    
    if request.method == 'POST':
        # 保存评分
        for question in questions:
            answer, created = Answer.objects.get_or_create(
                submission=segment.submission,
                question=question
            )
            
            score = request.POST.get(f'score_{question.id}', '0')
            feedback = request.POST.get(f'feedback_{question.id}', '')
            
            try:
                answer.score = float(score)
                answer.feedback = feedback
                answer.is_graded = True
                answer.save()
            except ValueError:
                messages.error(request, f'题目"{question.content[:30]}"的分数格式不正确。')
                return redirect('okr_exam:grade_segment', segment_id=segment_id)
        
        # 更新提交的总得分（即使未完全评完也要更新）
        total_score = Answer.objects.filter(
            submission=segment.submission,
            is_graded=True
        ).aggregate(models.Sum('score'))['score__sum'] or 0
        
        segment.submission.graded_score = total_score
        
        # 检查是否所有题目都已评分
        total_questions = Question.objects.filter(
            section__paper=segment.submission.paper
        ).count()
        
        graded_answers = Answer.objects.filter(
            submission=segment.submission,
            is_graded=True
        ).count()
        
        # 如果所有题目都已评分，标记为完成
        if graded_answers >= total_questions and total_questions > 0:
            segment.submission.is_graded = True
            segment.submission.graded_at = timezone.now()
        
        segment.submission.save()
        
        messages.success(request, '评分保存成功！')
        return redirect('okr_exam:grading_by_section')
    
    # 获取已有的答案
    answers = {
        answer.question_id: answer
        for answer in Answer.objects.filter(
            submission=segment.submission,
            question__in=questions
        )
    }
    
    return render(request, 'okr_exam/grade_segment.html', {
        'segment': segment,
        'questions': questions,
        'answers': answers
    })
