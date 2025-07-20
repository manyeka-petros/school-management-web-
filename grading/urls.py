from django.urls import path
from .views import (
    # Exam types
    ExamTypeListCreateAPIView,

    # Grades
    GradeListCreateAPIView,
    GradeDetailAPIView,

    # Exam records
    ManageExamListCreateAPIView,
    ManageExamDetailAPIView,
    MyExamsAPIView,

    # 🔸 Helper endpoints
    StudentsByClassroomAPIView,
    SubjectsByStudentAPIView,
)

urlpatterns = [
    # 🔹 Exam type list and create
    path("exam-types/", ExamTypeListCreateAPIView.as_view(), name="examtype-list-create"),

    # 🔹 Grade scale (CRUD)
    path("grades/", GradeListCreateAPIView.as_view(), name="grade-list-create"),
    path("grades/<int:pk>/", GradeDetailAPIView.as_view(), name="grade-detail"),

    # 🔹 Manage exam records
    path("exams/", ManageExamListCreateAPIView.as_view(), name="manageexam-list-create"),
    path("exams/<int:pk>/", ManageExamDetailAPIView.as_view(), name="manageexam-detail"),

    # 🔹 Exams for logged-in student
    path("exams/my/", MyExamsAPIView.as_view(), name="my-exams"),

    # 🔸 Helpers – for dynamic dropdowns in UI
    path("exams/helpers/students/", StudentsByClassroomAPIView.as_view(), name="students-by-classroom"),
    path("exams/helpers/subjects/", SubjectsByStudentAPIView.as_view(), name="subjects-by-student"),
]
