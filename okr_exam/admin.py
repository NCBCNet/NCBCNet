from django.contrib import admin
from .models import ExamPaper, PaperSection, Question, QuestionOption, ExamSubmission, Answer, SectionAssignment, ImageSegment


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 4


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    show_change_link = True


class PaperSectionInline(admin.TabularInline):
    model = PaperSection
    extra = 1
    show_change_link = True


class SectionAssignmentInline(admin.TabularInline):
    model = SectionAssignment
    extra = 1


@admin.register(ExamPaper)
class ExamPaperAdmin(admin.ModelAdmin):
    list_display = ['title', 'creator', 'total_score', 'duration', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    inlines = [PaperSectionInline]


@admin.register(PaperSection)
class PaperSectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'paper', 'order', 'region_x', 'region_y', 'region_width', 'region_height']
    list_filter = ['paper']
    search_fields = ['title', 'description']
    inlines = [QuestionInline, SectionAssignmentInline]
    fieldsets = (
        ('基本信息', {
            'fields': ('paper', 'title', 'description', 'order')
        }),
        ('图片分割区域设置 (百分比)', {
            'fields': ('region_x', 'region_y', 'region_width', 'region_height'),
            'description': '定义该分节在扫描试卷图片中的位置，使用百分比表示 (0-100)'
        }),
    )


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['content', 'section', 'question_type', 'score', 'order']
    list_filter = ['question_type', 'section__paper']
    search_fields = ['content']
    inlines = [QuestionOptionInline]


@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ['content', 'question', 'is_correct', 'order']
    list_filter = ['is_correct']
    search_fields = ['content']


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ['question', 'content', 'score', 'is_graded']


class ImageSegmentInline(admin.TabularInline):
    model = ImageSegment
    extra = 0
    readonly_fields = ['section', 'segment_image', 'x', 'y', 'width', 'height']


@admin.register(ExamSubmission)
class ExamSubmissionAdmin(admin.ModelAdmin):
    list_display = ['student', 'paper', 'is_scanned', 'is_segmented', 'is_submitted', 'is_graded', 'graded_score', 'started_at', 'submitted_at']
    list_filter = ['is_scanned', 'is_segmented', 'is_submitted', 'is_graded', 'paper']
    search_fields = ['student__username', 'paper__title']
    inlines = [ImageSegmentInline, AnswerInline]


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['submission', 'question', 'score', 'is_graded']
    list_filter = ['is_graded', 'question__question_type']
    search_fields = ['content', 'feedback']


@admin.register(SectionAssignment)
class SectionAssignmentAdmin(admin.ModelAdmin):
    list_display = ['section', 'teacher', 'assigned_at']
    list_filter = ['section__paper', 'teacher']
    search_fields = ['section__title', 'teacher__username']


@admin.register(ImageSegment)
class ImageSegmentAdmin(admin.ModelAdmin):
    list_display = ['submission', 'section', 'created_at']
    list_filter = ['section', 'created_at']
    readonly_fields = ['segment_image']
