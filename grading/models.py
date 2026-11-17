from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Exam(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "草稿"
        ACTIVE = "active", "评卷中"
        CLOSED = "closed", "已结束"

    name = models.CharField("考试名称", max_length=200)
    code = models.CharField("考试编码", max_length=64, unique=True)
    subject = models.CharField("科目", max_length=100)
    status = models.CharField("状态", max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_exams"
    )
    starts_at = models.DateTimeField("开始时间", null=True, blank=True)
    ends_at = models.DateTimeField("结束时间", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="questions")
    number = models.PositiveIntegerField("题号", validators=[MinValueValidator(1)])
    title = models.CharField("题目名称", max_length=200)
    max_score = models.DecimalField("满分", max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    rubric = models.JSONField("评分细则", default=dict, blank=True)
    is_objective = models.BooleanField("客观题", default=False)

    class Meta:
        ordering = ["number"]
        constraints = [
            models.UniqueConstraint(fields=["exam", "number"], name="unique_exam_question_number")
        ]

    def __str__(self):
        return f"{self.exam.code} - 第{self.number}题"


class ScanBatch(models.Model):
    class Status(models.TextChoices):
        RECEIVED = "received", "已接收"
        PROCESSING = "processing", "处理中"
        READY = "ready", "待分发"
        FAILED = "failed", "失败"

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="scan_batches")
    batch_no = models.CharField("批次号", max_length=100)
    source_file = models.FileField("扫描文件", upload_to="grading/scans/%Y/%m/%d/")
    status = models.CharField("状态", max_length=20, choices=Status.choices, default=Status.RECEIVED)
    page_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["exam", "batch_no"], name="unique_exam_batch_no")
        ]


class RecognitionJob(models.Model):
    class Status(models.TextChoices):
        QUEUED = "queued", "排队中"
        PROCESSING = "processing", "处理中"
        COMPLETED = "completed", "已完成"
        FAILED = "failed", "失败"

    batch = models.OneToOneField(ScanBatch, on_delete=models.CASCADE, related_name="recognition_job")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    engine = models.CharField(max_length=100, default="pillow-layout-v1")
    processed_pages = models.PositiveIntegerField(default=0)
    result = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveSmallIntegerField(default=0)
    max_retries = models.PositiveSmallIntegerField(default=3)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ExamTemplate(models.Model):
    exam = models.OneToOneField(Exam, on_delete=models.CASCADE, related_name="template")
    version = models.PositiveIntegerField(default=1)
    page_width = models.PositiveIntegerField(default=2480)
    page_height = models.PositiveIntegerField(default=3508)
    alignment_markers = models.JSONField(default=list, blank=True)
    blocks = models.JSONField(default=dict, blank=True)
    omr_regions = models.JSONField(default=list, blank=True)
    active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)


class ScanPage(models.Model):
    class Status(models.TextChoices):
        RECEIVED = "received", "已接收"
        NORMALIZED = "normalized", "已标准化"
        REVIEW = "review", "待复核"
        FAILED = "failed", "失败"

    batch = models.ForeignKey(ScanBatch, on_delete=models.CASCADE, related_name="pages")
    answer_sheet = models.ForeignKey(
        "AnswerSheet", on_delete=models.SET_NULL, null=True, blank=True, related_name="scan_pages"
    )
    page_no = models.PositiveIntegerField()
    source_image = models.ImageField(upload_to="grading/pages/%Y/%m/%d/")
    normalized_image = models.ImageField(upload_to="grading/normalized/%Y/%m/%d/", blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RECEIVED)
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    rotation = models.SmallIntegerField(default=0)
    quality = models.CharField(max_length=20, default="review")
    quality_reasons = models.JSONField(default=list, blank=True)
    ocr_result = models.JSONField(default=dict, blank=True)
    omr_result = models.JSONField(default=dict, blank=True)
    barcode_result = models.JSONField(default=dict, blank=True)
    alignment_result = models.JSONField(default=dict, blank=True)
    review_required = models.BooleanField(default=True)
    review_comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["batch_id", "page_no"]
        constraints = [
            models.UniqueConstraint(fields=["batch", "page_no"], name="unique_batch_page_no")
        ]


class Candidate(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="candidates")
    candidate_no = models.CharField("考号", max_length=100)
    barcode = models.CharField("条码", max_length=200)
    name = models.CharField("姓名", max_length=100, blank=True)

    class Meta:
        ordering = ["candidate_no"]
        constraints = [
            models.UniqueConstraint(fields=["exam", "candidate_no"], name="unique_exam_candidate_roster_no"),
            models.UniqueConstraint(fields=["exam", "barcode"], name="unique_exam_candidate_barcode"),
        ]


class AnswerSheet(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "待分发"
        GRADING = "grading", "评阅中"
        COMPLETED = "completed", "已完成"
        REVIEW = "review", "待复核"

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="answer_sheets")
    batch = models.ForeignKey(ScanBatch, on_delete=models.PROTECT, related_name="answer_sheets")
    candidate = models.ForeignKey(
        Candidate, on_delete=models.PROTECT, related_name="answer_sheets", null=True, blank=True
    )
    candidate_no = models.CharField("考号", max_length=100)
    page_image = models.ImageField("答题卡图像", upload_to="grading/sheets/%Y/%m/%d/", blank=True)
    status = models.CharField("状态", max_length=20, choices=Status.choices, default=Status.PENDING)
    objective_score = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    subjective_score = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["candidate_no"]
        constraints = [
            models.UniqueConstraint(fields=["exam", "candidate_no"], name="unique_exam_candidate_no")
        ]


class AnswerBlock(models.Model):
    class Status(models.TextChoices):
        READY = "ready", "待分发"
        ASSIGNED = "assigned", "已分发"
        REVIEW = "review", "待复核"

    answer_sheet = models.ForeignKey(AnswerSheet, on_delete=models.CASCADE, related_name="blocks")
    question = models.ForeignKey(Question, on_delete=models.PROTECT, related_name="answer_blocks")
    page = models.ForeignKey(ScanPage, on_delete=models.PROTECT, related_name="answer_blocks")
    image = models.ImageField(upload_to="grading/blocks/%Y/%m/%d/")
    bbox = models.JSONField(default=list)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.READY)
    quality = models.CharField(max_length=20, default="pass")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["answer_sheet", "question"], name="unique_sheet_question_block"
            )
        ]


class GradingAssignment(models.Model):
    class Status(models.TextChoices):
        ASSIGNED = "assigned", "待评阅"
        IN_PROGRESS = "in_progress", "评阅中"
        SUBMITTED = "submitted", "已提交"
        EXPIRED = "expired", "已过期"

    answer_sheet = models.ForeignKey(AnswerSheet, on_delete=models.CASCADE, related_name="assignments")
    question = models.ForeignKey(Question, on_delete=models.PROTECT, related_name="assignments")
    grader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="grading_assignments",
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ASSIGNED)
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    comment = models.TextField(blank=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    claimed_at = models.DateTimeField(null=True, blank=True)
    round_no = models.PositiveSmallIntegerField(default=1)
    arbitration_threshold = models.DecimalField(max_digits=6, decimal_places=2, default=2)
    answer_block = models.ForeignKey(
        AnswerBlock, on_delete=models.PROTECT, null=True, blank=True, related_name="assignments"
    )
    lease_expires_at = models.DateTimeField(null=True, blank=True)
    draft_score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    draft_comment = models.TextField(blank=True)

    class Meta:
        ordering = ["answer_sheet_id", "question__number"]
        permissions = [
            ("grade_answers", "可以评阅答题"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["answer_sheet", "question", "grader"], name="unique_grader_assignment"
            )
        ]


class GradingAuditLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=100)
    object_type = models.CharField(max_length=100)
    object_id = models.PositiveBigIntegerField()
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class TeacherProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="teacher_profile")
    subjects = models.JSONField(default=list, blank=True)
    question_numbers = models.JSONField(default=list, blank=True)
    max_active_assignments = models.PositiveIntegerField(default=50)
    enabled = models.BooleanField(default=True)


class QualityReview(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "待质检"
        PASSED = "passed", "通过"
        FAILED = "failed", "不通过"

    assignment = models.ForeignKey(GradingAssignment, on_delete=models.CASCADE, related_name="quality_reviews")
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="quality_reviews")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)


class ScoreSnapshot(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "草稿"
        LOCKED = "locked", "已锁定"
        RELEASED = "released", "已发布"

    answer_sheet = models.OneToOneField(AnswerSheet, on_delete=models.CASCADE, related_name="score_snapshot")
    total_score = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    objective_score = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    subjective_score = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)


class ReleaseApproval(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "待审批"
        APPROVED = "approved", "已批准"
        REJECTED = "rejected", "已驳回"
        PUBLISHED = "published", "已发布"
        REVOKED = "revoked", "已撤回"

    exam = models.OneToOneField(Exam, on_delete=models.CASCADE, related_name="release_approval")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="release_requests")
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="release_reviews")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    comment = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)


class ArbitrationCase(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "待仲裁"
        RESOLVED = "resolved", "已解决"

    answer_sheet = models.ForeignKey(AnswerSheet, on_delete=models.CASCADE, related_name="arbitration_cases")
    question = models.ForeignKey(Question, on_delete=models.PROTECT, related_name="arbitration_cases")
    assignments = models.ManyToManyField(GradingAssignment, related_name="arbitration_cases")
    threshold = models.DecimalField(max_digits=6, decimal_places=2, default=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    final_score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="resolved_arbitration_cases"
    )
    resolution_comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
