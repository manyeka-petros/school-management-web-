from django.urls import path
from .views import (
    RegisterView, LoginView,
    ProfileView, UpdateProfileView,
    GetAllStudentsTeachersView,
    CountUsersView,
    DeleteUserView,
    BlockUserView,
    CheckTokenView,
)

from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/update/', UpdateProfileView.as_view(), name='update-profile'),

    path('users/students-teachers/', GetAllStudentsTeachersView.as_view(), name='students-teachers'),
    path('users/count/', CountUsersView.as_view(), name='users-count'),
    path('users/<int:user_id>/delete/', DeleteUserView.as_view(), name='delete-user'),
    path('users/<int:user_id>/block/', BlockUserView.as_view(), name='block-user'),
    path('check-token/', CheckTokenView.as_view(), name='check-token'),

    # JWT token refresh and verify endpoints
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('users/<int:user_id>/delete/', DeleteUserView.as_view(), name='user-delete'),
]
