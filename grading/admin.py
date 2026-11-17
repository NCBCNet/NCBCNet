from django.contrib import admin

from .models import (
    AnswerSheet, ArbitrationCase, Exam, GradingAssignment, GradingAuditLog,
    QualityReview, Question, RecognitionJob, ReleaseApproval, ScanBatch,
    ScoreSnapshot, TeacherProfile,
)


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "subject", "status", "created_by", "created_at"]
    list_filter = ["status", "subject"]
    search_fields = ["name", "code"]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["exam", "number", "title", "max_score", "is_objective"]
    list_filter = ["is_objective", "exam"]


@admin.register(ScanBatch)
class ScanBatchAdmin(admin.ModelAdmin):
    list_display = ["batch_no", "exam", "status", "page_count", "uploaded_by", "created_at"]
    list_filter = ["status", "exam"]


@admin.register(RecognitionJob)
class RecognitionJobAdmin(admin.ModelAdmin):
    list_display = ["batch", "status", "engine", "processed_pages", "created_at", "completed_at"]
    list_filter = ["status", "engine"]
    readonly_fields = ["created_at", "started_at", "completed_at"]


@admin.register(AnswerSheet)
class AnswerSheetAdmin(admin.ModelAdmin):
    list_display = ["candidate_no", "exam", "status", "subjective_score", "created_at"]
    list_filter = ["status", "exam"]
    search_fields = ["candidate_no"]


@admin.register(GradingAssignment)
class GradingAssignmentAdmin(admin.ModelAdmin):
    list_display = ["answer_sheet", "question", "grader", "round_no", "status", "score", "submitted_at"]
    list_filter = ["status", "grader"]


@admin.register(ArbitrationCase)
class ArbitrationCaseAdmin(admin.ModelAdmin):
    list_display = ["answer_sheet", "question", "status", "threshold", "final_score", "resolved_by", "created_at"]
    list_filter = ["status"]
    readonly_fields = ["created_at", "resolved_at"]


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "max_active_assignments", "enabled"]
    list_filter = ["enabled"]


@admin.register(QualityReview)
class QualityReviewAdmin(admin.ModelAdmin):
    list_display = ["assignment", "reviewer", "status", "created_at", "reviewed_at"]
    list_filter = ["status", "reviewer"]


@admin.register(ScoreSnapshot)
class ScoreSnapshotAdmin(admin.ModelAdmin):
    list_display = ["answer_sheet", "total_score", "status", "version", "locked_at", "released_at"]
    list_filter = ["status"]
    readonly_fields = ["created_at", "locked_at", "released_at"]


@admin.register(ReleaseApproval)
class ReleaseApprovalAdmin(admin.ModelAdmin):
    list_display = ["exam", "status", "requested_by", "reviewed_by", "requested_at", "published_at"]
    list_filter = ["status"]
    readonly_fields = ["requested_at", "reviewed_at", "published_at"]


@admin.register(GradingAuditLog)
class GradingAuditLogAdmin(admin.ModelAdmin):
    list_display = ["action", "object_type", "object_id", "actor", "created_at"]
    list_filter = ["action", "object_type"]
    readonly_fields = ["actor", "action", "object_type", "object_id", "payload", "created_at"]
