from django.urls import path
from .views import (
    AnnouncementCreateView,
    AnnouncementListView,
    AnnouncementUpdateView,
    AnnouncementDeleteView,
    AnnouncementDetailView,
)

urlpatterns = [
    path('announcements/create/', AnnouncementCreateView.as_view(), name='announcement-create'),
    path('announcements/', AnnouncementListView.as_view(), name='announcement-list'),
    path('announcements/<int:pk>/', AnnouncementDetailView.as_view(), name='announcement-update'),
     path('announcements/update/<int:pk>/', AnnouncementUpdateView.as_view(), name='announcement-update'),
    path('announcements/delete/<int:pk>/', AnnouncementDeleteView.as_view(), name='announcement-delete'),
]
