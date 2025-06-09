from django.urls import path
from .views import BookAPIView, PastPaperAPIView

urlpatterns = [
    path('books/', BookAPIView.as_view(), name='books'),
    path('past-papers/', PastPaperAPIView.as_view(), name='past-papers'),
]
