# library/views.py
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

from .models import Book, BorrowedBook, Category
from .serializers import (
    BookSerializer,
    BorrowedBookSerializer,
    CategorySerializer,
)
from portalaccount.models import StudentProfile

User = get_user_model()
DEBUG_BORROW = False          # ↔ turn console prints on/off easily


# ------------------------------------------------------------------
# CATEGORY END‑POINTS
# ------------------------------------------------------------------
class CategoryListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        return Response(CategorySerializer(Category.objects.all(), many=True).data)

    def post(self, request):
        ser = CategorySerializer(data=request.data)
        if ser.is_valid():
            ser.save()
            return Response(ser.data, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


# ------------------------------------------------------------------
# BOOK END‑POINTS
# ------------------------------------------------------------------
class BookListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        qs = Book.objects.select_related("category")
        return Response(BookSerializer(qs, many=True).data)

    def post(self, request):
        ser = BookSerializer(data=request.data)
        if ser.is_valid():
            ser.save()
            return Response(ser.data, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class BookDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Book, pk=pk)

    def get(self, request, pk):
        return Response(BookSerializer(self.get_object(pk)).data)

    def put(self, request, pk):
        ser = BookSerializer(self.get_object(pk), data=request.data)
        if ser.is_valid():
            ser.save()
            return Response(ser.data)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        self.get_object(pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ------------------------------------------------------------------
# BORROW  /  RETURN
# ------------------------------------------------------------------
class BorrowBookCreateView(APIView):
    """
    POST payload (all strings):
        { user, book, issue_date, return_date, fine_per_day }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if DEBUG_BORROW:
            print("════ /borrow/ POST received ═══════")
            print("Payload:", request.data)

        # --- basic field presence ------------------------------------------------
        needed = ["user", "book", "issue_date", "return_date"]
        missing = [f for f in needed if not request.data.get(f)]
        if missing:
            return Response(
                {"detail": f"Missing field(s): {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- resolve relations ---------------------------------------------------
        user_obj = get_object_or_404(User, pk=request.data["user"])
        try:
            student = user_obj.student_profile
        except StudentProfile.DoesNotExist:
            return Response({"detail": "Student profile not found."}, status=404)

        book = get_object_or_404(Book, pk=request.data["book"])

        # --- guard: already borrowed & not yet returned --------------------------
        already = BorrowedBook.objects.filter(
            user=student, book=book, returned=False
        ).exists()
        if already:
            return Response(
                {"detail": "This book is already issued to the same student."},
                status=status.HTTP_409_CONFLICT,
            )

        # --- guard: copies available --------------------------------------------
        if book.available_copies <= 0:
            return Response(
                {"detail": "No available copies of this book."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- create borrow record atomically ------------------------------------
        with transaction.atomic():
            borrow = BorrowedBook.objects.create(
                user=student,
                book=book,
                issue_date=request.data["issue_date"],
                return_date=request.data["return_date"],
                returned=False,
            )
            # only now decrement stock
            book.available_copies -= 1
            book.save(update_fields=["available_copies"])

        ser = BorrowedBookSerializer(borrow)
        if DEBUG_BORROW:
            print("Serialized BorrowedBook:", ser.data)
        return Response(ser.data, status=status.HTTP_201_CREATED)


class ReturnBookAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        borrow = get_object_or_404(BorrowedBook, pk=pk)

        if borrow.returned:
            return Response(
                {"detail": "Book already returned."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            borrow.actual_return_date = timezone.now().date()
            borrow.returned = True
            borrow.save(update_fields=["actual_return_date", "returned"])

            borrow.book.available_copies += 1
            borrow.book.save(update_fields=["available_copies"])

        return Response(BorrowedBookSerializer(borrow).data)


# ------------------------------------------------------------------
# LISTING HELPERS
# ------------------------------------------------------------------
class MyBorrowedBooksAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        student = get_object_or_404(StudentProfile, user=request.user)
        qs = BorrowedBook.objects.filter(user=student).select_related("book")
        return Response(BorrowedBookSerializer(qs, many=True).data)


class AllBorrowedBooksAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = (
            BorrowedBook.objects.filter(returned=False)
            .select_related("user", "book")
            .order_by("-issue_date")
        )
        return Response(BorrowedBookSerializer(qs, many=True).data)
