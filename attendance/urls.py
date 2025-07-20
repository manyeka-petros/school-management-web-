from django.urls import path
from .views import AttendanceListCreateView

urlpatterns = [
    path('attendance/', AttendanceListCreateView.as_view(), name='attendance-list-create'),
]
