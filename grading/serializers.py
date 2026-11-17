from rest_framework import serializers

from .models import (
    AnswerBlock, AnswerSheet, ArbitrationCase, Candidate, Exam, ExamTemplate, GradingAssignment,
    QualityReview, Question, RecognitionJob, ReleaseApproval, ScanBatch, ScanPage,
    ScoreSnapshot, TeacherProfile, GradingAuditLog,
)


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "number", "title", "max_score", "rubric", "is_objective"]


class ExamSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Exam
        fields = ["id", "name", "code", "subject", "status", "starts_at", "ends_at", "questions"]
        read_only_fields = ["status"]


class ScanBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanBatch
        fields = ["id", "exam", "batch_no", "source_file", "status", "page_count", "error_message", "created_at"]
        read_only_fields = ["exam", "status", "error_message", "created_at"]


class AnswerSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerSheet
        fields = ["id", "exam", "batch", "candidate", "candidate_no", "page_image", "status", "objective_score", "subjective_score"]
        read_only_fields = ["exam", "status", "objective_score", "subjective_score"]

    def validate(self, attrs):
        exam = self.context["view"].kwargs.get("exam_id")
        batch = attrs.get("batch")
        if batch and str(batch.exam_id) != str(exam):
            raise serializers.ValidationError("批次与考试不匹配")
        candidate = attrs.get("candidate")
        if candidate and str(candidate.exam_id) != str(exam):
            raise serializers.ValidationError("考生与考试不匹配")
        if candidate:
            attrs["candidate_no"] = candidate.candidate_no
        return attrs


class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = ["id", "exam", "candidate_no", "barcode", "name"]
        read_only_fields = ["exam"]


class AssignmentSerializer(serializers.ModelSerializer):
    question_number = serializers.IntegerField(source="question.number", read_only=True)
    max_score = serializers.DecimalField(source="question.max_score", max_digits=6, decimal_places=2, read_only=True)
    candidate_no = serializers.CharField(source="answer_sheet.candidate_no", read_only=True)
    answer_sheet_image = serializers.ImageField(source="answer_sheet.page_image", read_only=True)
    answer_block_image = serializers.ImageField(source="answer_block.image", read_only=True)

    class Meta:
        model = GradingAssignment
        fields = ["id", "answer_sheet", "candidate_no", "answer_sheet_image", "answer_block_image", "question", "question_number", "max_score", "status", "score", "comment", "draft_score", "draft_comment", "assigned_at", "submitted_at", "claimed_at", "lease_expires_at", "round_no"]
        read_only_fields = ["status", "assigned_at", "submitted_at"]


class AssignmentSubmitSerializer(serializers.Serializer):
    score = serializers.DecimalField(max_digits=6, decimal_places=2, min_value=0)
    comment = serializers.CharField(required=False, allow_blank=True)


class AssignmentDraftSerializer(serializers.Serializer):
    score = serializers.DecimalField(max_digits=6, decimal_places=2, min_value=0, required=False, allow_null=True)
    comment = serializers.CharField(required=False, allow_blank=True)


class QualityReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityReview
        fields = ["id", "assignment", "reviewer", "status", "comment", "created_at", "reviewed_at"]
        read_only_fields = ["reviewer", "status", "created_at", "reviewed_at"]


class QualityReviewDecisionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[QualityReview.Status.PASSED, QualityReview.Status.FAILED])
    comment = serializers.CharField(required=False, allow_blank=True)


class TeacherProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherProfile
        fields = ["id", "user", "subjects", "question_numbers", "max_active_assignments", "enabled"]
        read_only_fields = ["user"]


class GradingAuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradingAuditLog
        fields = ["id", "actor", "action", "object_type", "object_id", "payload", "created_at"]
        read_only_fields = fields


class ScoreSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScoreSnapshot
        fields = ["id", "answer_sheet", "total_score", "objective_score", "subjective_score", "status", "version", "created_at", "locked_at", "released_at"]
        read_only_fields = fields


class ReleaseApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReleaseApproval
        fields = ["id", "exam", "requested_by", "reviewed_by", "status", "comment", "requested_at", "reviewed_at", "published_at"]
        read_only_fields = ["requested_by", "reviewed_by", "status", "requested_at", "reviewed_at", "published_at"]


class ReleaseDecisionSerializer(serializers.Serializer):
    approved = serializers.BooleanField()
    comment = serializers.CharField(required=False, allow_blank=True)


class DistributionSerializer(serializers.Serializer):
    grader_ids = serializers.ListField(child=serializers.IntegerField(min_value=1), min_length=1)
    question_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1), required=False, allow_empty=False
    )
    double_marking = serializers.BooleanField(default=True)
    arbitration_threshold = serializers.DecimalField(max_digits=6, decimal_places=2, min_value=0, default=2)


class RecognitionJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecognitionJob
        fields = ["id", "batch", "status", "engine", "processed_pages", "result", "error_message", "retry_count", "max_retries", "started_at", "completed_at"]
        read_only_fields = fields


class ExamTemplateSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        page_width = attrs.get("page_width", getattr(self.instance, "page_width", 0))
        page_height = attrs.get("page_height", getattr(self.instance, "page_height", 0))
        if page_width <= 0 or page_height <= 0:
            raise serializers.ValidationError("page_width 和 page_height 必须为正数")

        markers = attrs.get("alignment_markers", getattr(self.instance, "alignment_markers", []))
        if markers and len(markers) != 4:
            raise serializers.ValidationError("alignment_markers 必须包含四个定位点")
        for marker in markers:
            try:
                coordinates = (
                    (marker["x"], marker["y"])
                    if isinstance(marker, dict)
                    else (marker[0], marker[1])
                )
                x, y = [float(value) for value in coordinates]
            except (KeyError, IndexError, TypeError, ValueError):
                raise serializers.ValidationError("定位点必须是 {x, y} 或 [x, y]")
            if not (0 <= x < page_width and 0 <= y < page_height):
                raise serializers.ValidationError("定位点必须位于模板页面范围内")

        blocks = attrs.get("blocks", getattr(self.instance, "blocks", {}))
        if not isinstance(blocks, dict):
            raise serializers.ValidationError("blocks 必须是题号到坐标的对象")
        for box in blocks.values():
            if not self._valid_box(box, page_width, page_height):
                raise serializers.ValidationError("题块坐标必须是页面范围内的 [left, top, right, bottom]")

        regions = attrs.get("omr_regions", getattr(self.instance, "omr_regions", []))
        if not isinstance(regions, list):
            raise serializers.ValidationError("omr_regions 必须是数组")
        for region in regions:
            if not isinstance(region, dict) or not isinstance(region.get("options", []), list):
                raise serializers.ValidationError("每个 OMR 区域必须包含 options 数组")
            for option in region["options"]:
                if not isinstance(option, dict) or not self._valid_box(
                    option.get("bbox"), page_width, page_height
                ):
                    raise serializers.ValidationError("OMR 选项必须包含页面范围内的 bbox")
        return attrs

    @staticmethod
    def _valid_box(box, page_width, page_height):
        try:
            left, top, right, bottom = [float(value) for value in box]
        except (TypeError, ValueError):
            return False
        return 0 <= left < right <= page_width and 0 <= top < bottom <= page_height

    class Meta:
        model = ExamTemplate
        fields = ["id", "exam", "version", "page_width", "page_height", "alignment_markers", "blocks", "omr_regions", "active", "updated_at"]
        read_only_fields = ["exam", "updated_at"]


class ScanPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanPage
        fields = ["id", "batch", "answer_sheet", "page_no", "source_image", "normalized_image", "status", "width", "height", "rotation", "quality", "quality_reasons", "ocr_result", "omr_result", "barcode_result", "alignment_result", "review_required", "review_comment"]
        read_only_fields = fields


class ScanPageReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[ScanPage.Status.NORMALIZED, ScanPage.Status.REVIEW])
    comment = serializers.CharField(required=False, allow_blank=True)


class AnswerBlockSerializer(serializers.ModelSerializer):
    question_number = serializers.IntegerField(source="question.number", read_only=True)

    class Meta:
        model = AnswerBlock
        fields = ["id", "answer_sheet", "question", "question_number", "page", "image", "bbox", "status", "quality", "created_at"]
        read_only_fields = fields


class ArbitrationCaseSerializer(serializers.ModelSerializer):
    assignment_scores = serializers.SerializerMethodField()

    class Meta:
        model = ArbitrationCase
        fields = ["id", "answer_sheet", "question", "assignments", "assignment_scores", "threshold", "status", "final_score", "resolution_comment", "created_at", "resolved_at"]
        read_only_fields = ["assignments", "assignment_scores", "status", "final_score", "created_at", "resolved_at"]

    def get_assignment_scores(self, obj):
        return [
            {"assignment_id": assignment.id, "grader_id": assignment.grader_id, "score": assignment.score}
            for assignment in obj.assignments.all()
        ]


class ArbitrationResolveSerializer(serializers.Serializer):
    final_score = serializers.DecimalField(max_digits=6, decimal_places=2, min_value=0)
    resolution_comment = serializers.CharField(required=False, allow_blank=True)
