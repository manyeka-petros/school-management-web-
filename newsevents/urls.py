from django.urls import path
from .views import AnnouncementListCreate, AnnouncementDetail, AnnouncementFileDownload

urlpatterns = [
    path('announcements/', AnnouncementListCreate.as_view(), name='announcement-list-create'),
    path('announcements/<int:pk>/', AnnouncementDetail.as_view(), name='announcement-detail'),
    path('announcements/<int:pk>/download/', AnnouncementFileDownload.as_view(), name='announcement-file-download'),
]
