from django.urls import path
from .views import (
    RegisterView, LoginView,
    ProfileView, UpdateProfileView,
    GetAllStudents, GetAllTeachers, GetAllParents,
    GetAllStaff, GetAllHeadTeachers,
    GetAllUsers, CountUsers,
    DeleteUser, ToggleBlockUser,
    AssignRoleView, GetUnassignedUsers,
    CreateProfileView,
    RegisterStudentByHeadTeacherView  # <-- use this instead of FullStudentRegistrationView
)

from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    # Auth
    path('register/', RegisterView.as_view(), name='register'),  # Student self-signup
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # Profiles
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/create/', CreateProfileView.as_view(), name='create-profile'),
    path('profile/update/', UpdateProfileView.as_view(), name='update-profile'),

    # Full registration by Headteacher
    path('register/student/full/', RegisterStudentByHeadTeacherView.as_view(), name='full-student-register'),

    # Role-based user lists
    path('users/students/', GetAllStudents.as_view(), name='get-students'),
    path('users/teachers/', GetAllTeachers.as_view(), name='get-teachers'),
    path('users/parents/', GetAllParents.as_view(), name='get-parents'),
    path('users/staff/', GetAllStaff.as_view(), name='get-staff'),
    path('users/headteachers/', GetAllHeadTeachers.as_view(), name='get-headteachers'),

    # List all users and unassigned
    path('users/all/', GetAllUsers.as_view(), name='get-all-users'),
    path('users/unassigned/', GetUnassignedUsers.as_view(), name='unassigned-users'),

    # Count by role
    path('users/count/', CountUsers.as_view(), name='count-users'),

    # Headteacher/staff actions
    path('users/<int:user_id>/assign-role/', AssignRoleView.as_view(), name='assign-role'),
    path('users/<int:user_id>/delete/', DeleteUser.as_view(), name='delete-user'),
    path('users/<int:user_id>/block/', ToggleBlockUser.as_view(), name='block-user'),
]
