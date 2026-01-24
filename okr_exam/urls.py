from django.urls import path
from . import views

app_name = 'okr_exam'

urlpatterns = [
    path('', views.exam_list, name='exam_list'),
    path('exam/<int:paper_id>/', views.exam_detail, name='exam_detail'),
    path('exam/<int:paper_id>/start/', views.start_exam, name='start_exam'),
    path('exam/<int:paper_id>/upload/', views.upload_scanned_paper, name='upload_scanned_paper'),
    path('take/<int:submission_id>/', views.take_exam, name='take_exam'),
    path('segment/<int:submission_id>/', views.segment_scanned_paper, name='segment_scanned_paper'),
    path('submission/<int:submission_id>/', views.submission_detail, name='submission_detail'),
    path('grading/', views.grading_list, name='grading_list'),
    path('grading/<int:submission_id>/', views.grade_submission, name='grade_submission'),
    path('grading-by-section/', views.grading_by_section, name='grading_by_section'),
    path('grade-segment/<int:segment_id>/', views.grade_segment, name='grade_segment'),
    path('my-submissions/', views.my_submissions, name='my_submissions'),
]
