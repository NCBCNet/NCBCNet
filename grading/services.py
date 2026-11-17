from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import (
    AnswerBlock, AnswerSheet, ArbitrationCase, Candidate, Exam, ExamTemplate,
    GradingAssignment, GradingAuditLog, Question, QualityReview, RecognitionJob,
    ReleaseApproval, ScanBatch, ScanPage, ScoreSnapshot, TeacherProfile,
)
from .permissions import is_teacher
from .recognition import get_barcode_adapter, get_ocr_adapter, get_omr_adapter


@transaction.atomic
def distribute_assignments(*, exam, graders, question_ids=None, double_marking=True, arbitration_threshold=2):
    sheets = list(exam.answer_sheets.filter(status=AnswerSheet.Status.PENDING).order_by("id"))
    questions = list(exam.questions.filter(is_objective=False).order_by("number"))
    if question_ids is not None:
        questions = [question for question in questions if question.id in question_ids]
    graders = list(dict.fromkeys(graders))
    if any(not is_teacher(grader) for grader in graders):
        raise ValidationError("所有评卷人必须属于教师组")
    if not graders:
        raise ValidationError("至少需要一名评卷人")
    if not sheets or not questions:
        raise ValidationError("没有可分发的答题卡或主观题")
    profiles = {
        profile.user_id: profile
        for profile in TeacherProfile.objects.filter(user_id__in=[grader.id for grader in graders])
    }
    disabled = [grader.username for grader in graders if grader.id in profiles and not profiles[grader.id].enabled]
    if disabled:
        raise ValidationError(f"教师已停用，不能参与分发：{', '.join(disabled)}")
    active_counts = {
        grader.id: GradingAssignment.objects.filter(
            grader=grader, status=GradingAssignment.Status.IN_PROGRESS
        ).count()
        for grader in graders
    }
    capacities = {
        grader.id: profiles[grader.id].max_active_assignments
        if grader.id in profiles else None
        for grader in graders
    }

    def can_grade(grader, question):
        profile = profiles.get(grader.id)
        if not profile:
            return True
        if profile.subjects and exam.subject not in profile.subjects:
            return False
        return not profile.question_numbers or question.number in profile.question_numbers

    created = []
    for sheet in sheets:
        for question in questions:
            existing = GradingAssignment.objects.filter(answer_sheet=sheet, question=question)
            if existing.exists():
                continue
            marker = min(2 if double_marking else 1, len(graders))
            block = AnswerBlock.objects.filter(answer_sheet=sheet, question=question).first()
            selected = []
            for round_no in range(marker):
                eligible = [
                    grader for grader in graders
                    if grader.id not in selected
                    and can_grade(grader, question)
                    and (capacities[grader.id] is None or active_counts[grader.id] < capacities[grader.id])
                ]
                if not eligible:
                    raise ValidationError("可用教师容量不足，无法完成评卷分发")
                grader = min(eligible, key=lambda user: (active_counts[user.id], user.id))
                created.append(
                    GradingAssignment(
                        answer_sheet=sheet,
                        question=question,
                        grader=grader,
                        round_no=round_no + 1,
                        arbitration_threshold=arbitration_threshold,
                        answer_block=block,
                    )
                )
                selected.append(grader.id)
                active_counts[grader.id] += 1
        sheet.status = AnswerSheet.Status.GRADING
        sheet.save(update_fields=["status"])
    GradingAssignment.objects.bulk_create(created)
    GradingAuditLog.objects.create(
        actor=graders[0],
        action="distribute_assignments",
        object_type="exam",
        object_id=exam.id,
        payload={"created": len(created), "grader_ids": [user.id for user in graders]},
    )
    return created


@transaction.atomic
def process_scan_batch(*, batch_id):
    batch = ScanBatch.objects.select_for_update().get(pk=batch_id)
    job, _ = RecognitionJob.objects.get_or_create(batch=batch)
    if job.retry_count >= job.max_retries and job.status == RecognitionJob.Status.FAILED:
        raise ValidationError("识别任务已达到最大重试次数")
    job.status = RecognitionJob.Status.PROCESSING
    job.retry_count += 1
    job.started_at = timezone.now()
    job.error_message = ""
    job.save(update_fields=["status", "started_at", "error_message", "retry_count"])
    batch.status = ScanBatch.Status.PROCESSING
    batch.save(update_fields=["status"])
    try:
        pages = _extract_scan_pages(batch)
        results = []
        template = getattr(batch.exam, "template", None)
        if template and not template.active:
            raise ValidationError("考试模板未激活，不能开始识别")
        for page_no, image_bytes, original_name in pages:
            page = ScanPage.objects.filter(batch=batch, page_no=page_no).first()
            if not page:
                page = ScanPage(batch=batch, page_no=page_no)
            page.source_image.save(original_name, ContentFile(image_bytes), save=False)
            normalized_bytes, alignment = _normalize_image(image_bytes, template)
            page.normalized_image.save(
                f"{Path(original_name).stem}-normalized.png",
                ContentFile(normalized_bytes),
                save=False,
            )
            image_format, result = _analyze_image(normalized_bytes)
            page.width = result["width"]
            page.height = result["height"]
            page.quality = result["quality"]
            page.quality_reasons = result["quality_reasons"]
            page.ocr_result = _ocr_page(normalized_bytes)
            page.omr_result = _omr_page(normalized_bytes, template)
            barcode_result = _barcode_page(normalized_bytes)
            page.barcode_result = barcode_result
            page.alignment_result = alignment
            page.review_required = (
                result["quality"] == "review"
                or page.ocr_result.get("needs_review", True)
                or page.omr_result.get("needs_review", True)
            )
            page.status = ScanPage.Status.REVIEW if page.review_required else ScanPage.Status.NORMALIZED
            page.save()
            binding = _bind_barcode_candidate(batch, page, barcode_result)
            page.barcode_result = {**barcode_result, "binding": binding}
            if binding["needs_review"]:
                page.review_required = True
                page.status = ScanPage.Status.REVIEW
            page.save(update_fields=["barcode_result", "review_required", "status", "answer_sheet"])
            _create_answer_blocks(page, batch, template)
            result.update({
                "format": image_format, "page_no": page_no,
                "ocr": page.ocr_result, "omr": page.omr_result,
                "barcode": barcode_result,
                "candidate_binding": binding,
                "alignment": alignment,
            })
            results.append(result)
        job.result = {
            "pages": results,
            "page_count": len(results),
            **(results[0] if results else {}),
        }
        job.processed_pages = len(results)
        job.status = RecognitionJob.Status.COMPLETED
        job.completed_at = timezone.now()
        job.save(update_fields=["result", "processed_pages", "status", "completed_at"])
        batch.status = ScanBatch.Status.READY
        batch.page_count = len(results)
        batch.save(update_fields=["status", "page_count"])
        GradingAuditLog.objects.create(
            actor=batch.uploaded_by,
            action="recognize_scan_batch",
            object_type="scan_batch",
            object_id=batch.id,
            payload={
                "status": job.status,
                "processed_pages": len(results),
                "retry_count": job.retry_count,
            },
        )
    except Exception as exc:
        job.status = RecognitionJob.Status.FAILED
        job.error_message = str(exc)[:1000]
        job.save(update_fields=["status", "error_message"])
        batch.status = ScanBatch.Status.FAILED
        batch.error_message = job.error_message
        batch.save(update_fields=["status", "error_message"])
        GradingAuditLog.objects.create(
            actor=batch.uploaded_by,
            action="recognize_scan_batch_failed",
            object_type="scan_batch",
            object_id=batch.id,
            payload={"error": job.error_message, "retry_count": job.retry_count},
        )
        return job
    return job


def enqueue_scan_batch(*, batch_id):
    from core.tasks import get_queue

    job, _ = RecognitionJob.objects.get_or_create(batch_id=batch_id)
    job.status = RecognitionJob.Status.QUEUED
    job.save(update_fields=["status"])
    try:
        get_queue("grading").enqueue(process_scan_batch, batch_id=batch_id)
    except Exception:
        # 本地开发或 Redis 暂不可用时保持接口可用，退回当前进程执行。
        return process_scan_batch(batch_id=batch_id)
    return job


@transaction.atomic
def retry_scan_batch(*, batch_id):
    job = RecognitionJob.objects.select_for_update().get(batch_id=batch_id)
    if job.status != RecognitionJob.Status.FAILED:
        raise ValidationError("只有失败的识别任务可以重试")
    if job.retry_count >= job.max_retries:
        raise ValidationError("识别任务已达到最大重试次数")
    return enqueue_scan_batch(batch_id=batch_id)


@transaction.atomic
def review_scan_page(*, page_id, reviewer, status, comment=""):
    page = ScanPage.objects.select_for_update().get(pk=page_id)
    if status not in {ScanPage.Status.NORMALIZED, ScanPage.Status.REVIEW}:
        raise ValidationError("扫描页复核状态无效")
    page.status = status
    page.review_required = status == ScanPage.Status.REVIEW
    page.review_comment = comment
    page.save(update_fields=["status", "review_required", "review_comment"])
    GradingAuditLog.objects.create(
        actor=reviewer,
        action="review_scan_page",
        object_type="scan_page",
        object_id=page.id,
        payload={"status": status, "comment": comment},
    )
    return page


def _extract_scan_pages(batch):
    name = batch.source_file.name.lower()
    if name.endswith(".zip"):
        with ZipFile(batch.source_file) as archive:
            entries = sorted(
                item for item in archive.infolist()
                if not item.is_dir() and Path(item.filename).suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
            )
            return [(index, archive.read(item), Path(item.filename).name) for index, item in enumerate(entries, 1)]
    with batch.source_file.open("rb") as source:
        document = source.read()
    if name.endswith(".pdf"):
        return _render_pdf_pages(document, Path(name).stem or "page")
    if name.endswith((".tif", ".tiff")):
        return _render_tiff_pages(document, Path(name).stem or "page")
    return [(1, document, Path(name).name or "page-1.png")]


def _render_tiff_pages(document, stem):
    from PIL import Image

    pages = []
    with Image.open(BytesIO(document)) as source:
        for page_no in range(getattr(source, "n_frames", 1)):
            source.seek(page_no)
            frame = source.convert("RGB")
            output = BytesIO()
            frame.save(output, format="PNG")
            pages.append((page_no + 1, output.getvalue(), f"{stem}-{page_no + 1}.png"))
    return pages


def _render_pdf_pages(document, stem):
    try:
        import pymupdf as fitz
    except ImportError as exc:
        raise RuntimeError("PDF 识别需要安装 PyMuPDF（包名 pymupdf）") from exc

    pages = []
    with fitz.open(stream=document, filetype="pdf") as pdf:
        matrix = fitz.Matrix(2, 2)
        for page_no, page in enumerate(pdf, 1):
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            pages.append((page_no, pixmap.tobytes("png"), f"{stem}-{page_no}.png"))
    return pages


def _analyze_image(image_bytes):
    from PIL import Image, ImageOps

    with Image.open(BytesIO(image_bytes)) as source:
        image_format = source.format
        image = ImageOps.exif_transpose(source).convert("L")
        width, height = image.size
        thumbnail = image.copy()
        thumbnail.thumbnail((1000, 1000))
        histogram = thumbnail.histogram()
        dark_pixels = sum(histogram[:96])
        pixel_count = thumbnail.width * thumbnail.height
        ink_ratio = round(dark_pixels / pixel_count, 4) if pixel_count else 0
        content = ImageOps.invert(thumbnail).point(lambda value: 255 if value > 32 else 0)
        content_bbox = content.getbbox()
        reasons = [
            reason for reason, failed in [
                ("resolution_low", width < 1000 or height < 1000),
                ("blank_or_overexposed", ink_ratio <= 0.01),
                ("too_dark_or_noisy", ink_ratio >= 0.8),
                ("content_not_detected", content_bbox is None),
            ] if failed
        ]
        return image_format, {
            "width": width, "height": height,
            "orientation": "portrait" if height >= width else "landscape",
            "quality": "pass" if not reasons else "review",
            "quality_reasons": reasons, "ink_ratio": ink_ratio,
            "content_bbox": list(content_bbox) if content_bbox else None,
            "candidate_no": None, "engine_version": "pillow-layout-v2",
        }


def _normalize_image(image_bytes, template=None):
    from PIL import Image, ImageOps

    with Image.open(BytesIO(image_bytes)) as source:
        image = ImageOps.exif_transpose(source).convert("L")
        alignment = {"status": "not_configured", "markers": 0}
        markers = template.alignment_markers if template else []
        if len(markers) == 4:
            try:
                import cv2
                import numpy as np

                source_points = np.float32([
                    [float(marker["x"]), float(marker["y"])]
                    if isinstance(marker, dict)
                    else [float(marker[0]), float(marker[1])]
                    for marker in markers
                ])
                width = template.page_width
                height = template.page_height
                target_points = np.float32([
                    [0, 0], [width - 1, 0],
                    [width - 1, height - 1], [0, height - 1],
                ])
                matrix = cv2.getPerspectiveTransform(source_points, target_points)
                array = np.array(image)
                corrected = cv2.warpPerspective(array, matrix, (width, height))
                image = Image.fromarray(corrected)
                alignment = {"status": "corrected", "markers": 4}
            except (ImportError, KeyError, TypeError, ValueError):
                alignment = {"status": "fallback", "markers": 4}
        output = BytesIO()
        image.save(output, format="PNG", optimize=True)
        return output.getvalue(), alignment


def _ocr_page(image_bytes):
    return get_ocr_adapter().recognize(image_bytes)


def _omr_page(image_bytes, template):
    regions = template.omr_regions if template else []
    return get_omr_adapter().recognize(image_bytes, regions)


def _barcode_page(image_bytes):
    return get_barcode_adapter().recognize(image_bytes)


def _bind_barcode_candidate(batch, page, barcode_result):
    values = barcode_result.get("values", [])
    if not values:
        return {
            "status": "not_found",
            "candidate_id": None,
            "candidate_no": None,
            "needs_review": True,
        }
    if len(values) != 1:
        return {
            "status": "ambiguous",
            "candidate_id": None,
            "candidate_no": None,
            "barcodes": values,
            "needs_review": True,
        }
    barcode = values[0]
    candidate = Candidate.objects.filter(exam=batch.exam, barcode=barcode).first()
    if not candidate:
        return {
            "status": "unknown",
            "candidate_id": None,
            "candidate_no": None,
            "barcode": barcode,
            "needs_review": True,
        }
    sheet, created = AnswerSheet.objects.get_or_create(
        exam=batch.exam,
        candidate_no=candidate.candidate_no,
        defaults={
            "batch": batch,
            "candidate": candidate,
            "page_image": page.normalized_image.name,
        },
    )
    existing_pages = sheet.scan_pages.exclude(pk=page.pk)
    duplicate_batch = sheet.batch_id != batch.id
    duplicate_page = existing_pages.exists()
    if not sheet.candidate_id or not sheet.page_image:
        sheet.candidate = candidate
        if not sheet.page_image:
            sheet.page_image = page.normalized_image.name
        sheet.save(update_fields=["candidate", "page_image"])
    if page.answer_sheet_id != sheet.id:
        page.answer_sheet = sheet
        page.save(update_fields=["answer_sheet"])
    needs_review = duplicate_batch or duplicate_page
    return {
        "status": (
            "created" if created
            else "duplicate_batch" if duplicate_batch
            else "duplicate_page" if duplicate_page
            else "bound"
        ),
        "candidate_id": candidate.id,
        "candidate_no": candidate.candidate_no,
        "barcode": barcode,
        "answer_sheet_id": sheet.id,
        "duplicate_batch": duplicate_batch,
        "duplicate_page": duplicate_page,
        "needs_review": needs_review,
    }


def _create_answer_blocks(page, batch, template):
    from PIL import Image

    if not template:
        return
    for question_number, box in template.blocks.items():
        try:
            question = batch.exam.questions.get(number=int(question_number))
            left, top, right, bottom = [int(value) for value in box]
        except (ValueError, TypeError, Question.DoesNotExist):
            continue
        if not (0 <= left < right <= page.width and 0 <= top < bottom <= page.height):
            continue
        image_path = page.normalized_image.path if page.normalized_image else page.source_image.path
        with Image.open(image_path) as source:
            crop = source.crop((left, top, right, bottom))
            buffer = BytesIO()
            crop.save(buffer, format="PNG")
        sheet = page.answer_sheet or batch.answer_sheets.filter(page_image__isnull=False).first()
        if not sheet:
            continue
        block, _ = AnswerBlock.objects.get_or_create(
            answer_sheet=sheet, question=question,
            defaults={"page": page, "bbox": [left, top, right, bottom]},
        )
        if not block.image:
            block.image.save(
                f"sheet-{sheet.id}-q-{question.number}.png",
                ContentFile(buffer.getvalue()), save=True,
            )


@transaction.atomic
def claim_assignment(*, assignment_id, grader):
    assignment = GradingAssignment.objects.select_for_update().get(
        pk=assignment_id, grader=grader, status=GradingAssignment.Status.ASSIGNED
    )
    assignment.status = GradingAssignment.Status.IN_PROGRESS
    assignment.claimed_at = timezone.now()
    assignment.lease_expires_at = timezone.now() + timezone.timedelta(minutes=30)
    assignment.save(update_fields=["status", "claimed_at", "lease_expires_at"])
    return assignment


@transaction.atomic
def reclaim_expired_assignments(*, timeout_minutes=30):
    cutoff = timezone.now() - timezone.timedelta(minutes=timeout_minutes)
    assignments = GradingAssignment.objects.filter(
        status=GradingAssignment.Status.IN_PROGRESS,
    ).filter(Q(lease_expires_at__lt=timezone.now()) | Q(claimed_at__lt=cutoff))
    count = assignments.update(
        status=GradingAssignment.Status.ASSIGNED, claimed_at=None, lease_expires_at=None
    )
    return count


@transaction.atomic
def submit_assignment(*, assignment_id, grader, score, comment=""):
    assignment = (
        GradingAssignment.objects.select_for_update()
        .select_related("question", "answer_sheet")
        .get(pk=assignment_id, grader=grader)
    )
    if assignment.status == GradingAssignment.Status.SUBMITTED:
        raise ValidationError("该评卷任务已提交")
    if assignment.status != GradingAssignment.Status.IN_PROGRESS:
        raise ValidationError("请先领取评卷任务")
    score = Decimal(str(score))
    if score < 0 or score > assignment.question.max_score:
        raise ValidationError(f"分数必须在 0 至 {assignment.question.max_score} 之间")

    assignment.status = GradingAssignment.Status.SUBMITTED
    assignment.score = score
    assignment.comment = comment
    assignment.submitted_at = timezone.now()
    assignment.lease_expires_at = None
    assignment.save(update_fields=["status", "score", "comment", "submitted_at", "lease_expires_at"])

    sheet = AnswerSheet.objects.select_for_update().get(pk=assignment.answer_sheet_id)
    question_assignments = sheet.assignments.filter(question_id=assignment.question_id)
    submitted = list(question_assignments.filter(status=GradingAssignment.Status.SUBMITTED))
    if len(submitted) >= 2:
        scores = [item.score for item in submitted]
        threshold = assignment.arbitration_threshold
        if max(scores) - min(scores) > threshold:
            case, _ = ArbitrationCase.objects.get_or_create(
                answer_sheet=sheet, question_id=assignment.question_id,
                status=ArbitrationCase.Status.OPEN,
                defaults={"threshold": threshold},
            )
            case.assignments.set(submitted)
            sheet.status = AnswerSheet.Status.REVIEW
            sheet.save(update_fields=["status"])
        else:
            sheet.subjective_score = sum(scores) / len(scores)
            sheet.save(update_fields=["subjective_score"])
    pending = sheet.assignments.exclude(status=GradingAssignment.Status.SUBMITTED).exists()
    pending = pending or sheet.arbitration_cases.filter(status=ArbitrationCase.Status.OPEN).exists()
    if not pending:
        sheet.status = AnswerSheet.Status.COMPLETED
        sheet.subjective_score = sum(
            (item.score or Decimal("0")) for item in sheet.assignments.all()
        )
        sheet.save(update_fields=["status", "subjective_score"])

    GradingAuditLog.objects.create(
        actor=grader,
        action="submit_assignment",
        object_type="grading_assignment",
        object_id=assignment.id,
        payload={"score": str(score), "answer_sheet_id": sheet.id},
    )
    return assignment


@transaction.atomic
def save_assignment_draft(*, assignment_id, grader, score=None, comment=""):
    assignment = GradingAssignment.objects.select_for_update().get(
        pk=assignment_id, grader=grader, status=GradingAssignment.Status.IN_PROGRESS
    )
    if score is not None:
        score = Decimal(str(score))
        if score < 0 or score > assignment.question.max_score:
            raise ValidationError("草稿分数超出题目满分")
    assignment.draft_score = score
    assignment.draft_comment = comment
    assignment.save(update_fields=["draft_score", "draft_comment"])
    return assignment


@transaction.atomic
def renew_assignment_lease(*, assignment_id, grader):
    assignment = GradingAssignment.objects.select_for_update().get(
        pk=assignment_id, grader=grader, status=GradingAssignment.Status.IN_PROGRESS
    )
    assignment.lease_expires_at = timezone.now() + timezone.timedelta(minutes=30)
    assignment.save(update_fields=["lease_expires_at"])
    return assignment


@transaction.atomic
def create_quality_sample(*, exam, reviewer, sample_size=10):
    assignments = list(
        GradingAssignment.objects.filter(
            answer_sheet__exam=exam, status=GradingAssignment.Status.SUBMITTED
        ).order_by("?")[:sample_size]
    )
    reviews = [
        QualityReview(assignment=assignment, reviewer=reviewer)
        for assignment in assignments
        if not QualityReview.objects.filter(assignment=assignment).exists()
    ]
    QualityReview.objects.bulk_create(reviews)
    return reviews


@transaction.atomic
def review_assignment(*, review_id, reviewer, status, comment=""):
    review = QualityReview.objects.select_for_update().get(pk=review_id)
    if review.reviewer_id != reviewer.id:
        raise ValidationError("无权处理该质检任务")
    if status not in {QualityReview.Status.PASSED, QualityReview.Status.FAILED}:
        raise ValidationError("质检状态无效")
    review.status = status
    review.comment = comment
    review.reviewed_at = timezone.now()
    review.save(update_fields=["status", "comment", "reviewed_at"])
    GradingAuditLog.objects.create(
        actor=reviewer,
        action="review_quality",
        object_type="quality_review",
        object_id=review.id,
        payload={"status": status, "comment": comment, "assignment_id": review.assignment_id},
    )
    return review


@transaction.atomic
def create_score_snapshot(*, answer_sheet):
    if answer_sheet.status != AnswerSheet.Status.COMPLETED:
        raise ValidationError("答题卡尚未完成评阅")
    subjective = answer_sheet.subjective_score or Decimal("0")
    objective = answer_sheet.objective_score or Decimal("0")
    existing = ScoreSnapshot.objects.filter(answer_sheet=answer_sheet).first()
    if existing and existing.status in {ScoreSnapshot.Status.LOCKED, ScoreSnapshot.Status.RELEASED}:
        raise ValidationError("成绩快照已锁定，不能覆盖")
    snapshot, _ = ScoreSnapshot.objects.update_or_create(
        answer_sheet=answer_sheet,
        defaults={
            "total_score": objective + subjective,
            "objective_score": objective,
            "subjective_score": subjective,
            "status": ScoreSnapshot.Status.DRAFT,
            "version": existing.version + 1 if existing else 1,
        },
    )
    return snapshot


@transaction.atomic
def request_release(*, exam, requester, comment=""):
    sheets = exam.answer_sheets.all()
    if not sheets.exists() or sheets.exclude(status=AnswerSheet.Status.COMPLETED).exists():
        raise ValidationError("存在未完成评阅的答题卡")
    snapshots = ScoreSnapshot.objects.filter(answer_sheet__exam=exam)
    if snapshots.count() != sheets.count() or snapshots.exclude(
        status__in=[ScoreSnapshot.Status.DRAFT, ScoreSnapshot.Status.LOCKED]
    ).exists():
        raise ValidationError("存在未生成或已发布的成绩快照")
    snapshots.update(status=ScoreSnapshot.Status.LOCKED, locked_at=timezone.now())
    approval, _ = ReleaseApproval.objects.update_or_create(
        exam=exam, defaults={"requested_by": requester, "status": ReleaseApproval.Status.PENDING, "comment": comment}
    )
    GradingAuditLog.objects.create(
        actor=requester,
        action="request_release",
        object_type="release_approval",
        object_id=approval.id,
        payload={"exam_id": exam.id, "comment": comment},
    )
    return approval


@transaction.atomic
def decide_release(*, approval_id, reviewer, approved, comment=""):
    approval = ReleaseApproval.objects.select_for_update().get(pk=approval_id)
    approval.reviewed_by = reviewer
    approval.status = ReleaseApproval.Status.APPROVED if approved else ReleaseApproval.Status.REJECTED
    approval.comment = comment
    approval.reviewed_at = timezone.now()
    approval.save(update_fields=["reviewed_by", "status", "comment", "reviewed_at"])
    GradingAuditLog.objects.create(
        actor=reviewer,
        action="decide_release",
        object_type="release_approval",
        object_id=approval.id,
        payload={"approved": approved, "comment": comment},
    )
    return approval


@transaction.atomic
def publish_exam(*, approval_id, publisher):
    approval = ReleaseApproval.objects.select_for_update().get(
        pk=approval_id, status=ReleaseApproval.Status.APPROVED
    )
    ScoreSnapshot.objects.filter(answer_sheet__exam=approval.exam).update(
        status=ScoreSnapshot.Status.RELEASED, released_at=timezone.now()
    )
    approval.status = ReleaseApproval.Status.PUBLISHED
    approval.published_at = timezone.now()
    approval.save(update_fields=["status", "published_at"])
    approval.exam.status = Exam.Status.CLOSED
    approval.exam.save(update_fields=["status"])
    GradingAuditLog.objects.create(
        actor=publisher,
        action="publish_release",
        object_type="release_approval",
        object_id=approval.id,
        payload={"exam_id": approval.exam_id},
    )
    return approval


@transaction.atomic
def revoke_release(*, approval_id, revoker, comment=""):
    approval = ReleaseApproval.objects.select_for_update().get(
        pk=approval_id, status=ReleaseApproval.Status.PUBLISHED
    )
    ScoreSnapshot.objects.filter(answer_sheet__exam=approval.exam).update(
        status=ScoreSnapshot.Status.LOCKED,
        released_at=None,
    )
    approval.status = ReleaseApproval.Status.REVOKED
    approval.reviewed_by = revoker
    approval.comment = comment
    approval.reviewed_at = timezone.now()
    approval.save(update_fields=["status", "reviewed_by", "comment", "reviewed_at"])
    GradingAuditLog.objects.create(
        actor=revoker,
        action="revoke_release",
        object_type="release_approval",
        object_id=approval.id,
        payload={"exam_id": approval.exam_id, "comment": comment},
    )
    return approval


@transaction.atomic
def resolve_arbitration(*, case_id, resolver, final_score, resolution_comment=""):
    case = ArbitrationCase.objects.select_for_update().select_related("question", "answer_sheet").get(
        pk=case_id, status=ArbitrationCase.Status.OPEN
    )
    final_score = Decimal(str(final_score))
    if final_score < 0 or final_score > case.question.max_score:
        raise ValidationError("仲裁分数超出题目满分")
    case.status = ArbitrationCase.Status.RESOLVED
    case.final_score = final_score
    case.resolved_by = resolver
    case.resolution_comment = resolution_comment
    case.resolved_at = timezone.now()
    case.save(update_fields=["status", "final_score", "resolved_by", "resolution_comment", "resolved_at"])
    sheet = AnswerSheet.objects.select_for_update().get(pk=case.answer_sheet_id)
    scores = []
    for question_id in sheet.assignments.values_list("question_id", flat=True).distinct():
        question_case = sheet.arbitration_cases.filter(question_id=question_id, status=ArbitrationCase.Status.RESOLVED).first()
        if question_case:
            scores.append(question_case.final_score)
        else:
            submitted = list(sheet.assignments.filter(question_id=question_id, status=GradingAssignment.Status.SUBMITTED))
            if submitted:
                scores.append(sum(item.score for item in submitted) / len(submitted))
    sheet.subjective_score = sum(scores, Decimal("0"))
    if not sheet.arbitration_cases.filter(status=ArbitrationCase.Status.OPEN).exists() and not sheet.assignments.exclude(status=GradingAssignment.Status.SUBMITTED).exists():
        sheet.status = AnswerSheet.Status.COMPLETED
    else:
        sheet.status = AnswerSheet.Status.REVIEW
    sheet.save(update_fields=["subjective_score", "status"])
    GradingAuditLog.objects.create(
        actor=resolver, action="resolve_arbitration", object_type="arbitration_case",
        object_id=case.id, payload={"final_score": str(final_score)},
    )
    return case
