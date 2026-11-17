from decimal import Decimal
from io import BytesIO
from unittest.mock import Mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient

from .models import (
    AnswerBlock, AnswerSheet, ArbitrationCase, Candidate, Exam, ExamTemplate,
    GradingAssignment, GradingAuditLog, QualityReview, Question, ReleaseApproval, ScanBatch, ScanPage,
    ScoreSnapshot, TeacherProfile,
)
from .serializers import ExamTemplateSerializer
from .services import (
    claim_assignment, distribute_assignments, process_scan_batch,
    reclaim_expired_assignments, resolve_arbitration, submit_assignment,
    create_score_snapshot, decide_release, publish_exam, request_release,
    save_assignment_draft,
)
from .recognition import get_barcode_adapter, get_ocr_adapter, get_omr_adapter


class GradingWorkflowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="grader", password="test-password"
        )
        self.teacher_group, _ = Group.objects.get_or_create(name="教师")
        self.user.groups.add(self.teacher_group)
        self.outsider = get_user_model().objects.create_user(
            username="outsider", password="test-password"
        )
        self.exam = Exam.objects.create(
            name="2026 模拟考试", code="MOCK-2026", subject="数学", created_by=self.user
        )
        self.question = Question.objects.create(
            exam=self.exam, number=1, title="解答题", max_score=10
        )
        self.batch = ScanBatch.objects.create(
            exam=self.exam,
            batch_no="B001",
            source_file="grading/scans/b001.zip",
            uploaded_by=self.user,
        )
        self.sheet = AnswerSheet.objects.create(
            exam=self.exam, batch=self.batch, candidate_no="C001"
        )
        self.assignment = GradingAssignment.objects.create(
            answer_sheet=self.sheet, question=self.question, grader=self.user
        )

    def test_submit_assignment_updates_sheet_and_score(self):
        claim_assignment(assignment_id=self.assignment.id, grader=self.user)
        assignment = submit_assignment(
            assignment_id=self.assignment.id,
            grader=self.user,
            score=Decimal("8.5"),
            comment="步骤完整",
        )

        assignment.refresh_from_db()
        self.sheet.refresh_from_db()
        self.assertEqual(assignment.status, GradingAssignment.Status.SUBMITTED)
        self.assertEqual(assignment.score, Decimal("8.50"))
        self.assertEqual(self.sheet.status, AnswerSheet.Status.COMPLETED)
        self.assertEqual(self.sheet.subjective_score, Decimal("8.50"))

    def test_submit_assignment_rejects_score_above_maximum(self):
        from rest_framework.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            submit_assignment(
                assignment_id=self.assignment.id,
                grader=self.user,
                score=11,
            )

    def test_assignment_submit_api_requires_ownership(self):
        client = APIClient()
        client.force_authenticate(self.user)
        client.post(reverse("assignment-claim", kwargs={"pk": self.assignment.id}))
        response = client.post(
            reverse("assignment-submit", kwargs={"pk": self.assignment.id}),
            {"score": "7.5"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["score"], "7.50")

    def test_distribution_and_reclaim_cycle(self):
        self.assignment.delete()
        created = distribute_assignments(exam=self.exam, graders=[self.user])
        self.assertEqual(len(created), 1)
        claim_assignment(assignment_id=created[0].id, grader=self.user)
        self.assertEqual(reclaim_expired_assignments(timeout_minutes=0), 1)
        created[0].refresh_from_db()
        self.assertEqual(created[0].status, GradingAssignment.Status.ASSIGNED)

    def test_distribution_respects_disabled_teacher_profile(self):
        self.assignment.delete()
        TeacherProfile.objects.create(user=self.user, enabled=False)
        from rest_framework.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            distribute_assignments(exam=self.exam, graders=[self.user])

    def test_distribution_respects_teacher_subject_and_question_scope(self):
        self.assignment.delete()
        TeacherProfile.objects.create(user=self.user, subjects=["英语"], question_numbers=[2])
        from rest_framework.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            distribute_assignments(exam=self.exam, graders=[self.user])

    def test_non_owner_cannot_mutate_or_read_exam_resources(self):
        client = APIClient()
        client.force_authenticate(self.outsider)

        question_response = client.post(
            reverse("question-list", kwargs={"exam_id": self.exam.id}),
            {"number": 2, "title": "越权题目", "max_score": "5"},
            format="json",
        )
        stats_response = client.get(
            reverse("exam-statistics", kwargs={"pk": self.exam.id})
        )
        sheet_response = client.post(
            reverse("answer-sheet-list", kwargs={"exam_id": self.exam.id}),
            {"batch": self.batch.id, "candidate_no": "C002"},
            format="json",
        )

        self.assertEqual(question_response.status_code, 404)
        self.assertEqual(stats_response.status_code, 404)
        self.assertEqual(sheet_response.status_code, 404)

    def test_non_teacher_cannot_grade(self):
        client = APIClient()
        client.force_authenticate(self.outsider)
        response = client.get(reverse("my-assignments"))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_manage_teacher_profile(self):
        admin = get_user_model().objects.create_superuser(
            username="profile-admin", password="test-password", email="profile@example.com"
        )
        client = APIClient()
        client.force_authenticate(admin)
        response = client.get(reverse("teacher-profile-list"))
        self.assertEqual(response.status_code, 200)
        profile = response.data["results"][0] if isinstance(response.data, dict) else response.data[0]
        self.assertEqual(profile["user"], self.user.id)
        updated = client.patch(
            reverse("teacher-profile-detail", kwargs={"pk": profile["id"]}),
            {"enabled": False, "max_active_assignments": 20},
            format="json",
        )
        self.assertEqual(updated.status_code, 200)
        self.assertFalse(updated.data["enabled"])

    def test_admin_can_list_audit_logs(self):
        admin = get_user_model().objects.create_superuser(
            username="audit-admin", password="test-password", email="audit@example.com"
        )
        GradingAuditLog.objects.create(
            actor=admin, action="test_action", object_type="exam", object_id=self.exam.id,
        )
        client = APIClient()
        client.force_authenticate(admin)
        response = client.get(reverse("grading-audit-log-list"), {"action": "test_action"})
        self.assertEqual(response.status_code, 200)
        results = response.data["results"] if isinstance(response.data, dict) else response.data
        self.assertEqual(results[0]["action"], "test_action")

    def test_metrics_include_operations_health_counts(self):
        response = APIClient()
        admin = get_user_model().objects.create_superuser(
            username="metrics-admin", password="test-password", email="metrics@example.com"
        )
        response.force_authenticate(admin)
        result = response.get(reverse("grading-metrics"))
        self.assertEqual(result.status_code, 200)
        self.assertIn("failed_recognition_jobs", result.data)
        self.assertIn("pending_scan_page_reviews", result.data)
        self.assertIn("enabled_teachers", result.data)
        self.assertIn("teacher_load", result.data)
        self.assertIn("audit_events", result.data)

    def test_quality_review_writes_audit_log(self):
        review = QualityReview.objects.create(assignment=self.assignment, reviewer=self.user)
        from .services import review_assignment

        review_assignment(
            review_id=review.id,
            reviewer=self.user,
            status=QualityReview.Status.PASSED,
            comment="复核通过",
        )
        self.assertTrue(
            GradingAuditLog.objects.filter(
                action="review_quality", object_id=review.id, actor=self.user
            ).exists()
        )

    def test_double_marking_opens_arbitration(self):
        second_teacher = get_user_model().objects.create_user(
            username="grader-two", password="test-password"
        )
        second_teacher.groups.add(self.teacher_group)
        self.assignment.delete()
        assignments = distribute_assignments(
            exam=self.exam, graders=[self.user, second_teacher],
            double_marking=True, arbitration_threshold=1,
        )
        first, second = assignments[0], assignments[1]
        claim_assignment(assignment_id=first.id, grader=self.user)
        submit_assignment(assignment_id=first.id, grader=self.user, score=2)
        claim_assignment(assignment_id=second.id, grader=second_teacher)
        submit_assignment(assignment_id=second.id, grader=second_teacher, score=8)
        case = ArbitrationCase.objects.get(answer_sheet=self.sheet, question=self.question)
        self.assertEqual(case.status, ArbitrationCase.Status.OPEN)
        resolve_arbitration(case_id=case.id, resolver=self.user, final_score=6)
        self.sheet.refresh_from_db()
        self.assertEqual(self.sheet.status, AnswerSheet.Status.COMPLETED)
        self.assertEqual(self.sheet.subjective_score, Decimal("6"))

    def test_scan_recognition_records_layout_metadata(self):
        image_buffer = BytesIO()
        Image.new("RGB", (1024, 1400), "white").save(image_buffer, format="PNG")
        self.batch.source_file = SimpleUploadedFile(
            "sheet.png",
            image_buffer.getvalue(),
            content_type="image/png",
        )
        self.batch.save()
        job = process_scan_batch(batch_id=self.batch.id)
        self.assertEqual(job.status, "completed")
        self.assertEqual(job.result["orientation"], "portrait")
        self.assertEqual(ScanPage.objects.filter(batch=self.batch).count(), 1)
        page = ScanPage.objects.get(batch=self.batch)
        self.assertTrue(page.review_required)
        self.assertTrue(page.normalized_image.name)
        self.assertIn("status", page.barcode_result)
        self.assertIn("binding", page.barcode_result)
        self.assertIn("status", page.alignment_result)
        self.assertIn(get_ocr_adapter().name, {"unavailable", "tesseract"})
        self.assertIn(get_omr_adapter().name, {"unavailable", "opencv"})
        self.assertIn("barcode", job.result)
        self.assertIn(get_barcode_adapter().name, {"unavailable", "opencv-qr", "pyzbar", "hybrid-barcode"})

    def test_opencv_omr_recognizes_marked_option_when_available(self):
        if get_omr_adapter().name != "opencv":
            self.skipTest("OpenCV 未安装")
        import cv2
        import numpy as np

        image = np.full((120, 240), 255, dtype=np.uint8)
        cv2.circle(image, (50, 60), 25, 0, -1)
        cv2.circle(image, (150, 60), 25, 0, 2)
        _, encoded = cv2.imencode(".png", image)
        result = get_omr_adapter().recognize(encoded.tobytes(), [{
            "question": 1,
            "options": [
                {"key": "A", "bbox": [25, 35, 50, 50]},
                {"key": "B", "bbox": [125, 35, 50, 50]},
            ],
        }])
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["answers"][0]["selected"], "A")
        self.assertFalse(result["needs_review"])

    def test_opencv_omr_flags_ambiguous_marks_when_available(self):
        if get_omr_adapter().name != "opencv":
            self.skipTest("OpenCV 未安装")
        import cv2
        import numpy as np

        image = np.full((120, 240), 255, dtype=np.uint8)
        cv2.circle(image, (50, 60), 25, 0, -1)
        cv2.circle(image, (150, 60), 25, 0, -1)
        _, encoded = cv2.imencode(".png", image)
        result = get_omr_adapter().recognize(encoded.tobytes(), [{
            "question": 1,
            "options": [
                {"key": "A", "bbox": [25, 35, 50, 50]},
                {"key": "B", "bbox": [125, 35, 50, 50]},
            ],
        }])
        self.assertTrue(result["ambiguous"])
        self.assertTrue(result["needs_review"])

    def test_opencv_qr_round_trip_when_available(self):
        if get_barcode_adapter().name not in {"opencv-qr", "hybrid-barcode"}:
            self.skipTest("OpenCV QR 未安装")
        import cv2

        encoder = cv2.QRCodeEncoder_create()
        image = encoder.encode("BC-ROUNDTRIP")
        _, encoded = cv2.imencode(".png", image)
        result = get_barcode_adapter().recognize(encoded.tobytes())
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["values"], ["BC-ROUNDTRIP"])

    def test_hybrid_barcode_adapter_falls_back_to_pyzbar(self):
        from .recognition import HybridBarcodeAdapter

        primary = Mock()
        primary.recognize.return_value = {
            "values": [], "status": "not_found", "needs_review": True,
        }
        fallback = Mock()
        fallback.recognize.return_value = {
            "values": ["ONE-D-CODE"], "status": "completed", "needs_review": False,
            "engine": "pyzbar",
        }
        result = HybridBarcodeAdapter(primary, fallback).recognize(b"image")
        self.assertEqual(result["values"], ["ONE-D-CODE"])
        self.assertEqual(result["engine"], "pyzbar")
        fallback.recognize.assert_called_once_with(b"image")

    def test_pyzbar_qr_round_trip_when_system_library_available(self):
        try:
            import cv2
            from pyzbar.pyzbar import decode
        except (ImportError, OSError):
            self.skipTest("pyzbar 或系统 zbar 未安装")
        image = cv2.QRCodeEncoder_create().encode("PYZBAR-CHECK")
        _, encoded = cv2.imencode(
            ".png", cv2.resize(image, None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST)
        )
        decoded = decode(Image.open(BytesIO(encoded.tobytes())))
        self.assertEqual([item.data.decode() for item in decoded], ["PYZBAR-CHECK"])

    def test_pdf_scan_is_rendered_when_pymupdf_available(self):
        try:
            import pymupdf as fitz
        except ImportError:
            self.skipTest("PyMuPDF 未安装")
        pdf = fitz.open()
        page = pdf.new_page(width=400, height=600)
        page.insert_text((30, 80), "PDF SCAN")
        content = pdf.tobytes()
        pdf.close()
        self.batch.source_file = SimpleUploadedFile(
            "scan.pdf", content, content_type="application/pdf"
        )
        self.batch.save()
        job = process_scan_batch(batch_id=self.batch.id)
        self.assertEqual(job.status, "completed")
        self.assertEqual(job.processed_pages, 1)

    def test_tesseract_ocr_reads_printed_text_when_available(self):
        if get_ocr_adapter().name != "tesseract":
            self.skipTest("Tesseract 未安装")
        from PIL import ImageDraw

        image = Image.new("L", (900, 220), 255)
        ImageDraw.Draw(image).text((40, 70), "CANDIDATE 12345", fill=0)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        result = get_ocr_adapter().recognize(buffer.getvalue())
        self.assertIn("CANDIDATE", (result["text"] or "").upper())
        self.assertEqual(result["status"], "completed")

    def test_candidate_roster_binds_answer_sheet_and_rejects_other_exam(self):
        candidate = Candidate.objects.create(
            exam=self.exam, candidate_no="C002", barcode="BC002", name="测试考生"
        )
        client = APIClient()
        client.force_authenticate(self.user)
        response = client.post(
            reverse("answer-sheet-list", kwargs={"exam_id": self.exam.id}),
            {"batch": self.batch.id, "candidate": candidate.id, "candidate_no": "ignored"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["candidate_no"], "C002")
        other_exam = Exam.objects.create(
            name="Other", code="OTHER-2026", subject="数学", created_by=self.user
        )
        other_candidate = Candidate.objects.create(
            exam=other_exam, candidate_no="O001", barcode="OBC001"
        )
        response = client.post(
            reverse("answer-sheet-list", kwargs={"exam_id": self.exam.id}),
            {"batch": self.batch.id, "candidate": other_candidate.id, "candidate_no": "ignored"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_candidate_bulk_import_is_atomic_on_duplicates(self):
        client = APIClient()
        client.force_authenticate(self.user)
        response = client.post(
            reverse("candidate-import", kwargs={"exam_id": self.exam.id}),
            {"candidates": [
                {"candidate_no": "B001", "barcode": "BAR001", "name": "甲"},
                {"candidate_no": "B001", "barcode": "BAR002", "name": "乙"},
            ]},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Candidate.objects.filter(exam=self.exam).exists())
        response = client.post(
            reverse("candidate-import", kwargs={"exam_id": self.exam.id}),
            {"candidates": [
                {"candidate_no": "B001", "barcode": "BAR001", "name": "甲"},
                {"candidate_no": "B002", "barcode": "BAR002", "name": "乙"},
            ]},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["created"], 2)

    def test_known_barcode_binds_answer_sheet(self):
        candidate = Candidate.objects.create(
            exam=self.exam, candidate_no="C009", barcode="BC009"
        )
        image_buffer = BytesIO()
        Image.new("RGB", (1024, 1400), "white").save(image_buffer, format="PNG")
        self.batch.source_file = SimpleUploadedFile(
            "barcode.png", image_buffer.getvalue(), content_type="image/png"
        )
        self.batch.save()
        from .services import _bind_barcode_candidate

        page = ScanPage.objects.create(
            batch=self.batch, page_no=1, source_image=SimpleUploadedFile(
                "page.png", image_buffer.getvalue(), content_type="image/png"
            ),
            normalized_image=SimpleUploadedFile(
                "normalized.png", image_buffer.getvalue(), content_type="image/png"
            ),
        )
        result = _bind_barcode_candidate(
            self.batch, page, {"values": ["BC009"], "status": "completed"}
        )
        self.assertEqual(result["status"], "created")
        self.assertEqual(result["candidate_no"], candidate.candidate_no)
        self.assertTrue(
            AnswerSheet.objects.filter(
                exam=self.exam, candidate=candidate, candidate_no="C009"
            ).exists()
        )
        page.refresh_from_db()
        self.assertEqual(page.answer_sheet.candidate_id, candidate.id)

    def test_scan_recognition_expands_multipage_tiff(self):
        first = Image.new("RGB", (1024, 1400), "white")
        second = Image.new("RGB", (1024, 1400), "white")
        image_buffer = BytesIO()
        first.save(image_buffer, format="TIFF", save_all=True, append_images=[second])
        self.batch.source_file = SimpleUploadedFile(
            "sheets.tiff",
            image_buffer.getvalue(),
            content_type="image/tiff",
        )
        self.batch.save()

        job = process_scan_batch(batch_id=self.batch.id)

        self.assertEqual(job.status, "completed")
        self.assertEqual(job.processed_pages, 2)
        self.assertEqual(ScanPage.objects.filter(batch=self.batch).count(), 2)
        self.assertEqual(
            list(ScanPage.objects.filter(batch=self.batch).order_by("page_no").values_list("page_no", flat=True)),
            [1, 2],
        )

    def test_scan_page_review_writes_audit_log(self):
        image_buffer = BytesIO()
        Image.new("RGB", (1024, 1400), "white").save(image_buffer, format="PNG")
        self.batch.source_file = SimpleUploadedFile(
            "review.png", image_buffer.getvalue(), content_type="image/png"
        )
        self.batch.save()
        process_scan_batch(batch_id=self.batch.id)
        page = ScanPage.objects.get(batch=self.batch)
        from .services import review_scan_page

        review_scan_page(
            page_id=page.id,
            reviewer=self.user,
            status=ScanPage.Status.NORMALIZED,
            comment="人工确认页面可用",
        )
        self.assertTrue(
            GradingAuditLog.objects.filter(
                action="review_scan_page", object_id=page.id, actor=self.user
            ).exists()
        )

    def test_admin_can_list_scan_page_review_queue(self):
        admin = get_user_model().objects.create_superuser(
            username="scan-review-admin", password="test-password", email="scan@example.com"
        )
        ScanPage.objects.create(
            batch=self.batch,
            page_no=1,
            source_image="grading/pages/review.png",
            review_required=True,
        )
        client = APIClient()
        client.force_authenticate(admin)
        response = client.get(reverse("scan-page-review-queue"))
        self.assertEqual(response.status_code, 200)
        results = response.data["results"] if isinstance(response.data, dict) else response.data
        self.assertEqual(len(results), 1)
        filtered = client.get(
            reverse("scan-page-review-queue"), {"batch_id": self.batch.id + 1}
        )
        filtered_results = (
            filtered.data["results"] if isinstance(filtered.data, dict) else filtered.data
        )
        self.assertEqual(filtered_results, [])

    def test_barcode_binding_marks_duplicate_scan_page_for_review(self):
        candidate = Candidate.objects.create(
            exam=self.exam, candidate_no="C001", barcode="BAR-C001"
        )
        page = ScanPage.objects.create(
            batch=self.batch, page_no=1, source_image="grading/pages/one.png"
        )
        from .services import _bind_barcode_candidate

        first = _bind_barcode_candidate(
            self.batch, page, {"values": ["BAR-C001"]}
        )
        self.assertFalse(first["needs_review"])
        duplicate = ScanPage.objects.create(
            batch=self.batch, page_no=2, source_image="grading/pages/two.png"
        )
        result = _bind_barcode_candidate(
            self.batch, duplicate, {"values": ["BAR-C001"]}
        )
        self.assertEqual(result["status"], "duplicate_page")
        self.assertTrue(result["needs_review"])

    def test_barcode_binding_marks_multiple_values_ambiguous(self):
        page = ScanPage.objects.create(
            batch=self.batch, page_no=1, source_image="grading/pages/ambiguous.png"
        )
        from .services import _bind_barcode_candidate

        result = _bind_barcode_candidate(
            self.batch, page, {"values": ["BAR-1", "BAR-2"]}
        )
        self.assertEqual(result["status"], "ambiguous")
        self.assertTrue(result["needs_review"])

    def test_failed_recognition_is_persisted_for_retry(self):
        self.batch.source_file = "grading/scans/missing.png"
        self.batch.save()
        job = process_scan_batch(batch_id=self.batch.id)
        self.assertEqual(job.status, "failed")
        job.refresh_from_db()
        self.assertEqual(job.retry_count, 1)

    def test_admin_can_list_failed_recognition_jobs(self):
        self.batch.source_file = "grading/scans/missing.png"
        self.batch.save()
        process_scan_batch(batch_id=self.batch.id)
        admin = get_user_model().objects.create_superuser(
            username="recognition-admin", password="test-password", email="recognition@example.com"
        )
        client = APIClient()
        client.force_authenticate(admin)
        response = client.get(reverse("recognition-job-failed-list"))
        self.assertEqual(response.status_code, 200)
        results = response.data["results"] if isinstance(response.data, dict) else response.data
        self.assertEqual(results[0]["batch"], self.batch.id)

    def test_template_creates_question_block(self):
        image_buffer = BytesIO()
        Image.new("RGB", (1024, 1400), "white").save(image_buffer, format="PNG")
        content = image_buffer.getvalue()
        self.batch.source_file = SimpleUploadedFile("sheet.png", content, content_type="image/png")
        self.batch.save()
        self.sheet.page_image.save("sheet.png", SimpleUploadedFile("sheet.png", content, content_type="image/png"))
        ExamTemplate.objects.create(
            exam=self.exam,
            blocks={"1": [0, 0, 500, 500]},
        )
        process_scan_batch(batch_id=self.batch.id)
        block = AnswerBlock.objects.get(answer_sheet=self.sheet, question=self.question)
        self.assertEqual(block.bbox, [0, 0, 500, 500])
        self.assertTrue(block.image.name)

    def test_template_serializer_rejects_invalid_geometry(self):
        serializer = ExamTemplateSerializer(data={
            "page_width": 400,
            "page_height": 600,
            "alignment_markers": [{"x": 1, "y": 1}],
            "blocks": {"1": [0, 0, 500, 500]},
            "omr_regions": [],
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("alignment_markers", str(serializer.errors))

        serializer = ExamTemplateSerializer(data={
            "page_width": 400,
            "page_height": 600,
            "alignment_markers": [],
            "blocks": {"1": [0, 0, 500, 500]},
            "omr_regions": [],
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("题块坐标", str(serializer.errors))

    def test_template_update_writes_audit_log(self):
        template = ExamTemplate.objects.create(exam=self.exam)
        client = APIClient()
        client.force_authenticate(self.user)
        response = client.patch(
            reverse("exam-template", kwargs={"exam_id": self.exam.id}),
            {"version": 2, "active": False},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            GradingAuditLog.objects.filter(
                action="update_exam_template",
                object_id=template.id,
                actor=self.user,
            ).exists()
        )

    def test_scan_rejects_inactive_exam_template(self):
        ExamTemplate.objects.create(exam=self.exam, active=False)
        image_buffer = BytesIO()
        Image.new("RGB", (1024, 1400), "white").save(image_buffer, format="PNG")
        self.batch.source_file = SimpleUploadedFile(
            "inactive-template.png", image_buffer.getvalue(), content_type="image/png"
        )
        self.batch.save()
        job = process_scan_batch(batch_id=self.batch.id)
        self.assertEqual(job.status, "failed")
        self.assertIn("模板未激活", job.error_message)
        self.assertTrue(
            GradingAuditLog.objects.filter(
                action="recognize_scan_batch_failed",
                object_id=self.batch.id,
            ).exists()
        )

    def test_template_alignment_markers_perspective_corrects_when_opencv_available(self):
        if get_omr_adapter().name != "opencv":
            self.skipTest("OpenCV 未安装")
        ExamTemplate.objects.create(
            exam=self.exam,
            page_width=400,
            page_height=600,
            alignment_markers=[
                {"x": 20, "y": 30}, {"x": 980, "y": 20},
                {"x": 1000, "y": 1370}, {"x": 10, "y": 1380},
            ],
        )
        image_buffer = BytesIO()
        Image.new("RGB", (1024, 1400), "white").save(image_buffer, format="PNG")
        self.batch.source_file = SimpleUploadedFile(
            "aligned.png", image_buffer.getvalue(), content_type="image/png"
        )
        self.batch.save()
        job = process_scan_batch(batch_id=self.batch.id)
        self.assertEqual(job.result["alignment"]["status"], "corrected")
        self.assertEqual(job.result["alignment"]["markers"], 4)

    def test_draft_and_release_workflow(self):
        claim_assignment(assignment_id=self.assignment.id, grader=self.user)
        save_assignment_draft(
            assignment_id=self.assignment.id, grader=self.user, score=Decimal("9"), comment="草稿"
        )
        submit_assignment(assignment_id=self.assignment.id, grader=self.user, score=Decimal("9"))
        self.sheet.refresh_from_db()
        snapshot = create_score_snapshot(answer_sheet=self.sheet)
        self.assertEqual(snapshot.total_score, Decimal("9"))
        approval = request_release(exam=self.exam, requester=self.user)
        self.assertEqual(approval.status, ReleaseApproval.Status.PENDING)
        approval = decide_release(approval_id=approval.id, reviewer=self.user, approved=True)
        publish_exam(approval_id=approval.id, publisher=self.user)
        snapshot.refresh_from_db()
        self.exam.refresh_from_db()
        self.assertEqual(snapshot.status, ScoreSnapshot.Status.RELEASED)
        self.assertEqual(self.exam.status, Exam.Status.CLOSED)
        from rest_framework.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            create_score_snapshot(answer_sheet=self.sheet)

    def test_release_requires_all_answer_sheets_completed(self):
        claim_assignment(assignment_id=self.assignment.id, grader=self.user)
        submit_assignment(assignment_id=self.assignment.id, grader=self.user, score=Decimal("9"))
        self.sheet.refresh_from_db()
        create_score_snapshot(answer_sheet=self.sheet)
        AnswerSheet.objects.create(
            exam=self.exam, batch=self.batch, candidate_no="C002",
        )
        from rest_framework.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            request_release(exam=self.exam, requester=self.user)

    def test_release_decision_requires_explicit_approval_and_exports_scores(self):
        claim_assignment(assignment_id=self.assignment.id, grader=self.user)
        submit_assignment(assignment_id=self.assignment.id, grader=self.user, score=Decimal("9"))
        self.sheet.refresh_from_db()
        create_score_snapshot(answer_sheet=self.sheet)
        approval = request_release(exam=self.exam, requester=self.user)

        client = APIClient()
        admin = get_user_model().objects.create_superuser(
            username="admin", password="test-password", email="admin@example.com"
        )
        client.force_authenticate(admin)
        rejected = client.post(
            reverse("release-decision", kwargs={"pk": approval.id}),
            {"approved": False, "comment": "数据需要复核"},
            format="json",
        )
        self.assertEqual(rejected.status_code, 200)
        self.assertEqual(rejected.data["status"], ReleaseApproval.Status.REJECTED)

        approval = request_release(exam=self.exam, requester=self.user)
        approved = client.post(
            reverse("release-decision", kwargs={"pk": approval.id}),
            {"approved": True},
            format="json",
        )
        self.assertEqual(approved.status_code, 200)
        client.post(reverse("release-publish", kwargs={"pk": approval.id}))
        exported = client.get(reverse("exam-score-export", kwargs={"pk": self.exam.id}))
        self.assertEqual(exported.status_code, 200)
        self.assertIn("C001", exported.content.decode("utf-8-sig"))
        scores = client.get(
            reverse("exam-scores", kwargs={"pk": self.exam.id}),
            {"candidate_no": "C001"},
        )
        self.assertEqual(scores.status_code, 200)
        self.assertEqual(scores.data[0]["candidate_no"], "C001")

        revoked = client.post(reverse("release-revoke", kwargs={"pk": approval.id}))
        self.assertEqual(revoked.status_code, 200)
        self.assertEqual(revoked.data["status"], ReleaseApproval.Status.REVOKED)
        self.assertEqual(
            client.get(reverse("exam-score-export", kwargs={"pk": self.exam.id})).status_code,
            409,
        )
        self.assertTrue(
            GradingAuditLog.objects.filter(
                action="publish_release", object_id=approval.id, actor=admin
            ).exists()
        )
        self.assertTrue(
            GradingAuditLog.objects.filter(
                action="revoke_release", object_id=approval.id, actor=admin
            ).exists()
        )
