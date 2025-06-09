from django.urls import path
from .views import (
    ClassroomListCreate,
    SubjectCreate,
    SubjectEnrollStudent,
    GradeCreate,
    GradeCreateOrUpdate,
    StudentGrades,
    ClassroomStudents,
    TeacherProfileView,
    StudentProfileView,
    TeacherDashboardView,
    SubjectListForStudents,
    EnrollInSubject,
    EnrolledSubjectsView,
    AllSubjectsView,
    GradeDetailOrList,
    
)

urlpatterns = [
    # Classroom
    path('classrooms/', ClassroomListCreate.as_view(), name='classroom-list-create'),
    path('classrooms/<int:classroom_id>/students/', ClassroomStudents.as_view(), name='classroom-students'),

    # Subject
    path('subjects/create/', SubjectCreate.as_view(), name='subject-create'),
    path('subjects/<int:subject_id>/enroll-student/', SubjectEnrollStudent.as_view(), name='subject-enroll-student'),
    path('subjects/', SubjectListForStudents.as_view(), name='subject-list-for-students'),
    path('subjects/<int:subject_id>/enroll/', EnrollInSubject.as_view(), name='enroll-in-subject'),
    path('subjects/enrolled/', EnrolledSubjectsView.as_view(), name='enrolled-subjects'),
     path('subjects/all/', AllSubjectsView.as_view(), name='all-subjects'),
    # Grade
    path('grades/create/', GradeCreate.as_view(), name='grade-create'),
    path('grades/create-or-update/', GradeCreateOrUpdate.as_view(), name='grade-create-or-update'),
    path('grades/student/', StudentGrades.as_view(), name='student-grades'),

    # Profiles
    path('teachers/me/', TeacherProfileView.as_view(), name='teacher-profile'),
    path('students/me/', StudentProfileView.as_view(), name='student-profile'),
    path('grades/', GradeDetailOrList.as_view(), name='grade-list'),
    path('grades/<int:grade_id>/', GradeDetailOrList.as_view(), name='grade-detail'),

    # Dashboard
    path('teacher-dashboard/', TeacherDashboardView.as_view(), name='teacher-dashboard'),
]
