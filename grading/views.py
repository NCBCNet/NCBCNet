import csv
import io

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    AnswerBlock, AnswerSheet, ArbitrationCase, Candidate, Exam, ExamTemplate, GradingAssignment,
    QualityReview, Question, RecognitionJob, ReleaseApproval, ScanBatch, ScanPage,
    ScoreSnapshot, TeacherProfile, GradingAuditLog,
)
from .permissions import IsTeacher
from .serializers import (
    AnswerSheetSerializer,
    AssignmentSerializer,
    AssignmentSubmitSerializer,
    ExamTemplateSerializer,
    ExamSerializer,
    QuestionSerializer, ScanPageReviewSerializer,
    ScanPageSerializer,
    AnswerBlockSerializer,
    ScanBatchSerializer,
    DistributionSerializer,
    ArbitrationCaseSerializer, ArbitrationResolveSerializer, RecognitionJobSerializer,
    AssignmentDraftSerializer, QualityReviewDecisionSerializer, QualityReviewSerializer, ReleaseApprovalSerializer,
    ReleaseDecisionSerializer, ScoreSnapshotSerializer, TeacherProfileSerializer,
    GradingAuditLogSerializer,
    CandidateSerializer,
)
from .services import (
    claim_assignment, create_score_snapshot, create_quality_sample, decide_release,
    distribute_assignments, enqueue_scan_batch, process_scan_batch, publish_exam,
    reclaim_expired_assignments, renew_assignment_lease, request_release,
    resolve_arbitration, review_assignment, revoke_release, save_assignment_draft, submit_assignment,
    review_scan_page, retry_scan_batch,
)


class ExamListCreateView(generics.ListCreateAPIView):
    serializer_class = ExamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Exam.objects.prefetch_related("questions")
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ExamDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = ExamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Exam.objects.prefetch_related("questions")
        return queryset if self.request.user.is_staff else queryset.filter(created_by=self.request.user)


class QuestionListCreateView(generics.ListCreateAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Question.objects.filter(exam_id=self.kwargs["exam_id"])
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(exam__created_by=self.request.user)

    def perform_create(self, serializer):
        exam = self._owned_exam()
        serializer.save(exam=exam)

    def _owned_exam(self):
        queryset = Exam.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(created_by=self.request.user)
        return get_object_or_404(queryset, pk=self.kwargs["exam_id"])


class ScanBatchCreateView(generics.ListCreateAPIView):
    serializer_class = ScanBatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ScanBatch.objects.filter(exam_id=self.kwargs["exam_id"])
        return queryset if self.request.user.is_staff else queryset.filter(exam__created_by=self.request.user)

    def perform_create(self, serializer):
        exam = self._owned_exam()
        serializer.save(exam=exam, uploaded_by=self.request.user)

    def _owned_exam(self):
        queryset = Exam.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(created_by=self.request.user)
        return get_object_or_404(queryset, pk=self.kwargs["exam_id"])


class AnswerSheetListView(generics.ListCreateAPIView):
    serializer_class = AnswerSheetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = AnswerSheet.objects.filter(exam_id=self.kwargs["exam_id"]).select_related("batch")
        return queryset if self.request.user.is_staff else queryset.filter(exam__created_by=self.request.user)

    def perform_create(self, serializer):
        exam = self._owned_exam()
        serializer.save(exam=exam)

    def _owned_exam(self):
        queryset = Exam.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(created_by=self.request.user)
        return get_object_or_404(queryset, pk=self.kwargs["exam_id"])


class CandidateListCreateView(generics.ListCreateAPIView):
    serializer_class = CandidateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Candidate.objects.filter(exam_id=self.kwargs["exam_id"])
        return queryset if self.request.user.is_staff else queryset.filter(exam__created_by=self.request.user)

    def perform_create(self, serializer):
        queryset = Exam.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(created_by=self.request.user)
        exam = get_object_or_404(queryset, pk=self.kwargs["exam_id"])
        serializer.save(exam=exam)


class CandidateBulkImportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, exam_id):
        queryset = Exam.objects.all()
        if not request.user.is_staff:
            queryset = queryset.filter(created_by=request.user)
        exam = get_object_or_404(queryset, pk=exam_id)
        rows = request.data.get("candidates")
        if rows is None and request.FILES.get("file"):
            content = request.FILES["file"].read().decode("utf-8-sig")
            rows = list(csv.DictReader(io.StringIO(content)))
        if not isinstance(rows, list) or not rows:
            return Response({"detail": "请提供 candidates 数组或 CSV 文件"}, status=status.HTTP_400_BAD_REQUEST)

        normalized = []
        seen_numbers = set()
        seen_barcodes = set()
        for row in rows:
            candidate_no = str(row.get("candidate_no", "")).strip()
            barcode = str(row.get("barcode", "")).strip()
            if not candidate_no or not barcode:
                return Response({"detail": "candidate_no 和 barcode 不能为空"}, status=status.HTTP_400_BAD_REQUEST)
            if candidate_no in seen_numbers or barcode in seen_barcodes:
                return Response({"detail": "导入数据中存在重复考号或条码"}, status=status.HTTP_400_BAD_REQUEST)
            seen_numbers.add(candidate_no)
            seen_barcodes.add(barcode)
            normalized.append({
                "candidate_no": candidate_no,
                "barcode": barcode,
                "name": str(row.get("name", "")).strip(),
            })

        conflicts = Candidate.objects.filter(exam=exam).filter(
            Q(candidate_no__in=seen_numbers) | Q(barcode__in=seen_barcodes)
        )
        if conflicts.exists():
            return Response({"detail": "考号或条码已存在，未导入任何记录"}, status=status.HTTP_409_CONFLICT)
        Candidate.objects.bulk_create([Candidate(exam=exam, **row) for row in normalized])
        return Response({"created": len(normalized)}, status=status.HTTP_201_CREATED)


class MyAssignmentListView(generics.ListAPIView):
    serializer_class = AssignmentSerializer
    permission_classes = [IsTeacher]

    def get_queryset(self):
        return GradingAssignment.objects.filter(grader=self.request.user).select_related(
            "question", "answer_sheet"
        )


class AssignmentClaimView(APIView):
    permission_classes = [IsTeacher]

    def post(self, request, pk):
        assignment = claim_assignment(assignment_id=pk, grader=request.user)
        return Response(AssignmentSerializer(assignment).data)


class AssignmentDistributionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        exam = get_object_or_404(Exam, pk=pk)
        if exam.created_by_id != request.user.id and not request.user.is_staff:
            return Response({"detail": "无权操作该考试"}, status=status.HTTP_403_FORBIDDEN)
        serializer = DistributionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        users = list(
            get_user_model()
            .objects.filter(
                id__in=serializer.validated_data["grader_ids"],
                is_active=True,
                groups__name="教师",
            )
            .distinct()
        )
        if len(users) != len(set(serializer.validated_data["grader_ids"])):
            return Response({"detail": "评卷人不存在或已禁用"}, status=status.HTTP_400_BAD_REQUEST)
        assignments = distribute_assignments(
            exam=exam,
            graders=users,
            question_ids=serializer.validated_data.get("question_ids"),
            double_marking=serializer.validated_data["double_marking"],
            arbitration_threshold=serializer.validated_data["arbitration_threshold"],
        )
        return Response({"created": len(assignments)}, status=status.HTTP_201_CREATED)


class AssignmentReclaimView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        timeout = int(request.data.get("timeout_minutes", 30))
        return Response({"reclaimed": reclaim_expired_assignments(timeout_minutes=timeout)})


class AssignmentSubmitView(APIView):
    permission_classes = [IsTeacher]

    def post(self, request, pk):
        serializer = AssignmentSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assignment = submit_assignment(
            assignment_id=pk,
            grader=request.user,
            **serializer.validated_data,
        )
        return Response(AssignmentSerializer(assignment).data)


class AssignmentDraftView(APIView):
    permission_classes = [IsTeacher]

    def patch(self, request, pk):
        serializer = AssignmentDraftSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assignment = save_assignment_draft(
            assignment_id=pk, grader=request.user, **serializer.validated_data
        )
        return Response(AssignmentSerializer(assignment).data)


class AssignmentLeaseView(APIView):
    permission_classes = [IsTeacher]

    def post(self, request, pk):
        assignment = renew_assignment_lease(assignment_id=pk, grader=request.user)
        return Response(AssignmentSerializer(assignment).data)


class ScanRecognitionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        batch = get_object_or_404(ScanBatch, pk=pk)
        if not request.user.is_staff and batch.exam.created_by_id != request.user.id:
            return Response({"detail": "无权操作该批次"}, status=status.HTTP_403_FORBIDDEN)
        if request.query_params.get("async") == "true":
            job = enqueue_scan_batch(batch_id=batch.id)
        else:
            job = process_scan_batch(batch_id=batch.id)
        return Response(RecognitionJobSerializer(job).data)

    def get(self, request, pk):
        job = get_object_or_404(RecognitionJob, batch_id=pk)
        if not request.user.is_staff and job.batch.exam.created_by_id != request.user.id:
            return Response({"detail": "无权查看该任务"}, status=status.HTTP_403_FORBIDDEN)
        return Response(RecognitionJobSerializer(job).data)


class ScanRecognitionRetryView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        try:
            job = retry_scan_batch(batch_id=pk)
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(RecognitionJobSerializer(job).data, status=status.HTTP_202_ACCEPTED)


class ScanRecognitionJobListView(generics.ListAPIView):
    serializer_class = RecognitionJobSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = RecognitionJob.objects.select_related("batch", "batch__exam").order_by("-created_at")

    def get_queryset(self):
        return super().get_queryset().filter(status=RecognitionJob.Status.FAILED)[:100]


class ExamTemplateView(generics.RetrieveUpdateAPIView):
    serializer_class = ExamTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        queryset = ExamTemplate.objects.filter(exam_id=self.kwargs["exam_id"])
        if not self.request.user.is_staff:
            queryset = queryset.filter(exam__created_by=self.request.user)
        return get_object_or_404(queryset)

    def perform_update(self, serializer):
        template = serializer.save(exam_id=self.kwargs["exam_id"])
        GradingAuditLog.objects.create(
            actor=self.request.user,
            action="update_exam_template",
            object_type="exam_template",
            object_id=template.id,
            payload={
                "exam_id": template.exam_id,
                "version": template.version,
                "active": template.active,
            },
        )


class ScanPageListView(generics.ListAPIView):
    serializer_class = ScanPageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ScanPage.objects.filter(batch_id=self.kwargs["batch_id"]).select_related("batch__exam")
        if not self.request.user.is_staff:
            queryset = queryset.filter(batch__exam__created_by=self.request.user)
        return queryset


class ScanPageReviewQueueView(generics.ListAPIView):
    serializer_class = ScanPageSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = ScanPage.objects.filter(review_required=True).select_related(
        "batch", "batch__exam", "answer_sheet"
    ).order_by("batch_id", "page_no")

    def get_queryset(self):
        queryset = super().get_queryset()
        exam_id = self.request.query_params.get("exam_id")
        batch_id = self.request.query_params.get("batch_id")
        if exam_id:
            queryset = queryset.filter(batch__exam_id=exam_id)
        if batch_id:
            queryset = queryset.filter(batch_id=batch_id)
        return queryset


class ScanPageReviewView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        serializer = ScanPageReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        page = review_scan_page(
            page_id=pk,
            reviewer=request.user,
            **serializer.validated_data,
        )
        return Response(ScanPageSerializer(page).data)


class AnswerBlockListView(generics.ListAPIView):
    serializer_class = AnswerBlockSerializer
    permission_classes = [IsTeacher]

    def get_queryset(self):
        return AnswerBlock.objects.filter(
            answer_sheet__assignments__grader=self.request.user
        ).select_related("question", "page").distinct()


class ArbitrationListView(generics.ListAPIView):
    serializer_class = ArbitrationCaseSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return ArbitrationCase.objects.filter(status=ArbitrationCase.Status.OPEN).prefetch_related("assignments")


class ArbitrationResolveView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        serializer = ArbitrationResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        case = resolve_arbitration(case_id=pk, resolver=request.user, **serializer.validated_data)
        return Response(ArbitrationCaseSerializer(case).data)


class QualityReviewListView(generics.ListAPIView):
    serializer_class = QualityReviewSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return QualityReview.objects.filter(status=QualityReview.Status.PENDING).select_related("assignment")


class QualitySampleView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        exam = get_object_or_404(Exam, pk=pk)
        size = int(request.data.get("sample_size", 10))
        reviews = create_quality_sample(exam=exam, reviewer=request.user, sample_size=max(1, min(size, 1000)))
        return Response({"created": len(reviews)}, status=status.HTTP_201_CREATED)


class QualityReviewDetailView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        serializer = QualityReviewDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = review_assignment(
            review_id=pk,
            reviewer=request.user,
            **serializer.validated_data,
        )
        return Response(QualityReviewSerializer(review).data)


class ExamSnapshotView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        exam = get_object_or_404(Exam, pk=pk)
        snapshots = [
            create_score_snapshot(answer_sheet=sheet)
            for sheet in exam.answer_sheets.filter(status=AnswerSheet.Status.COMPLETED)
        ]
        return Response({"created": len(snapshots)})

    def get(self, request, pk):
        snapshots = ScoreSnapshot.objects.filter(answer_sheet__exam_id=pk)
        return Response(ScoreSnapshotSerializer(snapshots, many=True).data)


class ExamReleaseView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        exam = get_object_or_404(Exam, pk=pk)
        approval = request_release(exam=exam, requester=request.user, comment=request.data.get("comment", ""))
        return Response(ReleaseApprovalSerializer(approval).data, status=status.HTTP_201_CREATED)


class ReleaseApprovalListView(generics.ListAPIView):
    serializer_class = ReleaseApprovalSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = ReleaseApproval.objects.select_related("exam", "requested_by", "reviewed_by")


class ReleaseDecisionView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        serializer = ReleaseDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        approval = decide_release(
            approval_id=pk,
            reviewer=request.user,
            approved=request.data.get("approved", False),
            comment=serializer.validated_data.get("comment", ""),
        )
        return Response(ReleaseApprovalSerializer(approval).data)


class ReleasePublishView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        approval = publish_exam(approval_id=pk, publisher=request.user)
        return Response(ReleaseApprovalSerializer(approval).data)


class ReleaseRevokeView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        approval = revoke_release(
            approval_id=pk,
            revoker=request.user,
            comment=request.data.get("comment", "管理员撤回已发布成绩"),
        )
        return Response(ReleaseApprovalSerializer(approval).data)


class TeacherProfileListView(generics.ListAPIView):
    serializer_class = TeacherProfileSerializer
    permission_classes = [permissions.IsAdminUser]
    def get_queryset(self):
        teacher_group = Group.objects.filter(name="教师").first()
        if teacher_group:
            for user in teacher_group.user_set.all():
                TeacherProfile.objects.get_or_create(user=user)
        return TeacherProfile.objects.select_related("user").order_by("user__username")


class TeacherProfileDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = TeacherProfileSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = TeacherProfile.objects.select_related("user")
    http_method_names = ["get", "patch", "head", "options"]


class GradingAuditLogListView(generics.ListAPIView):
    serializer_class = GradingAuditLogSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        queryset = GradingAuditLog.objects.select_related("actor").order_by("-created_at")
        action = self.request.query_params.get("action")
        if action:
            queryset = queryset.filter(action=action)
        return queryset[:100]


class ExamScoreExportView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, pk):
        exam = get_object_or_404(Exam, pk=pk)
        approval = getattr(exam, "release_approval", None)
        if not approval or approval.status != ReleaseApproval.Status.PUBLISHED:
            return Response({"detail": "成绩尚未发布"}, status=status.HTTP_409_CONFLICT)

        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{exam.code}-scores.csv"'
        response.write("\ufeff")
        writer = csv.writer(response)
        writer.writerow(["考号", "客观题得分", "主观题得分", "总分", "快照版本"])
        snapshots = ScoreSnapshot.objects.filter(
            answer_sheet__exam=exam,
            status=ScoreSnapshot.Status.RELEASED,
        ).select_related("answer_sheet").order_by("answer_sheet__candidate_no")
        for snapshot in snapshots:
            writer.writerow([
                snapshot.answer_sheet.candidate_no,
                snapshot.objective_score,
                snapshot.subjective_score,
                snapshot.total_score,
                snapshot.version,
            ])
        return response


class ExamScoresView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        queryset = Exam.objects.all()
        if not request.user.is_staff:
            queryset = queryset.filter(created_by=request.user)
        exam = get_object_or_404(queryset, pk=pk)
        approval = getattr(exam, "release_approval", None)
        if not approval or approval.status != ReleaseApproval.Status.PUBLISHED:
            return Response({"detail": "成绩尚未发布"}, status=status.HTTP_409_CONFLICT)
        snapshots = ScoreSnapshot.objects.filter(
            answer_sheet__exam=exam,
            status=ScoreSnapshot.Status.RELEASED,
        ).select_related("answer_sheet").order_by("answer_sheet__candidate_no")
        candidate_no = request.query_params.get("candidate_no")
        if candidate_no:
            snapshots = snapshots.filter(answer_sheet__candidate_no=candidate_no)
        return Response([
            {
                "candidate_no": snapshot.answer_sheet.candidate_no,
                "total_score": snapshot.total_score,
                "objective_score": snapshot.objective_score,
                "subjective_score": snapshot.subjective_score,
                "version": snapshot.version,
                "released_at": snapshot.released_at,
            }
            for snapshot in snapshots
        ])


class GradingMetricsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        return Response({
            "exams": Exam.objects.count(),
            "scan_batches": ScanBatch.objects.count(),
            "scan_jobs": {
                status: RecognitionJob.objects.filter(status=status).count()
                for status, _ in RecognitionJob.Status.choices
            },
            "assignments": {
                status: GradingAssignment.objects.filter(status=status).count()
                for status, _ in GradingAssignment.Status.choices
            },
            "open_arbitrations": ArbitrationCase.objects.filter(
                status=ArbitrationCase.Status.OPEN
            ).count(),
            "pending_quality_reviews": QualityReview.objects.filter(
                status=QualityReview.Status.PENDING
            ).count(),
            "released_snapshots": ScoreSnapshot.objects.filter(
                status=ScoreSnapshot.Status.RELEASED
            ).count(),
            "failed_recognition_jobs": RecognitionJob.objects.filter(
                status=RecognitionJob.Status.FAILED
            ).count(),
            "pending_scan_page_reviews": ScanPage.objects.filter(review_required=True).count(),
            "enabled_teachers": TeacherProfile.objects.filter(enabled=True).count(),
            "teacher_load": [
                {
                    "profile_id": profile.id,
                    "user_id": profile.user_id,
                    "username": profile.user.username,
                    "active_assignments": profile.active_assignments,
                    "max_active_assignments": profile.max_active_assignments,
                    "enabled": profile.enabled,
                }
                for profile in TeacherProfile.objects.select_related("user").annotate(
                    active_assignments=Count(
                        "user__grading_assignments",
                        filter=Q(user__grading_assignments__status=GradingAssignment.Status.IN_PROGRESS),
                    )
                ).order_by("user__username")
            ],
            "audit_events": GradingAuditLog.objects.count(),
        })


class ExamStatisticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        queryset = Exam.objects.all()
        if not request.user.is_staff:
            queryset = queryset.filter(created_by=request.user)
        exam = get_object_or_404(queryset, pk=pk)
        sheets = exam.answer_sheets.all()
        assignments = GradingAssignment.objects.filter(answer_sheet__exam=exam)
        return Response({
            "exam_id": exam.id,
            "status": exam.status,
            "answer_sheets": sheets.count(),
            "completed_sheets": sheets.filter(status=AnswerSheet.Status.COMPLETED).count(),
            "assignments": assignments.count(),
            "submitted_assignments": assignments.filter(status=GradingAssignment.Status.SUBMITTED).count(),
            "total_subjective_score": assignments.filter(
                status=GradingAssignment.Status.SUBMITTED
            ).aggregate(total=Sum("score"))["total"] or 0,
        })
