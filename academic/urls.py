from django.urls import path
from .views import (
    ClassroomListCreate,
    SubjectListCreate,
    AssignClassroomSubject,
    EnrollInClassroom,
    StudentSubjectsView,
    ClassroomDetailsAPIView,
    MyAssignedSubjectsView,  # NEW ↩
)

urlpatterns = [
    # core CRUD
    path("classrooms/",             ClassroomListCreate.as_view()),
    path("subjects/",               SubjectListCreate.as_view()),
    path("assign-subject/",         AssignClassroomSubject.as_view()),

    # enrolment
    path("enroll/",                 EnrollInClassroom.as_view()),

    # subjects for learners
    path("my-subjects/",                       StudentSubjectsView.as_view()),
    path("student-subjects/<int:uid>/",        StudentSubjectsView.as_view()),
    path("my-assigned-subjects/",              MyAssignedSubjectsView.as_view()),  # NEW ↩

    # extra helpers
    path("classroom-details/<int:pk>/",        ClassroomDetailsAPIView.as_view()),
]
