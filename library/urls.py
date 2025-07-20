from django.urls import path
from .views import (
    CategoryListCreateAPIView,
    BookListCreateAPIView,
    BookDetailAPIView,
    BorrowBookCreateView,
    ReturnBookAPIView,
    MyBorrowedBooksAPIView,
    AllBorrowedBooksAPIView
)

urlpatterns = [
    path('categories/', CategoryListCreateAPIView.as_view(), name='category-list-create'),
    path('books/', BookListCreateAPIView.as_view(), name='book-list-create'),
    path('books/<int:pk>/', BookDetailAPIView.as_view(), name='book-detail'),
    path('borrow/', BorrowBookCreateView.as_view(), name='borrow-book'),  # ✅ Correct endpoint
    path('return/<int:pk>/', ReturnBookAPIView.as_view(), name='return-book'),
    path('my-borrowed/', MyBorrowedBooksAPIView.as_view(), name='my-borrowed-books'),
    path('borrowed/all/', AllBorrowedBooksAPIView.as_view(), name='all-borrowed-books'),
]
