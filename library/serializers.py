from rest_framework import serializers
from django.utils import timezone
from .models import Book, BorrowedBook, Category
from portalaccount.models import StudentProfile
from django.contrib.auth import get_user_model

User = get_user_model()

# ────────────────────────────────────────────────────────
# CATEGORY SERIALIZER
# ────────────────────────────────────────────────────────
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']


# ────────────────────────────────────────────────────────
# BOOK SERIALIZER
# ────────────────────────────────────────────────────────
class BookSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'description', 'file', 'isbn',
            'author', 'publisher', 'edition',
            'price', 'language', 'total_copies', 'available_copies',
            'uploaded_at', 'category'
        ]
        read_only_fields = ['available_copies', 'uploaded_at']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['category'] = CategorySerializer(instance.category).data if instance.category else None
        return rep


# ────────────────────────────────────────────────────────
# BORROWED BOOK SERIALIZER
# ────────────────────────────────────────────────────────
class BorrowedBookSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    book_title = serializers.SerializerMethodField()

    is_overdue = serializers.ReadOnlyField()
    overdue_days = serializers.ReadOnlyField()
    fine = serializers.ReadOnlyField()

    overdue = serializers.SerializerMethodField()  # Backward compatibility
    fine_per_day = serializers.SerializerMethodField()  # Optional field if needed

    class Meta:
        model = BorrowedBook
        fields = [
            'id', 'user', 'user_name',
            'book', 'book_title',
            'issue_date', 'return_date', 'actual_return_date',
            'returned',

            # Calculated
            'is_overdue', 'overdue', 'overdue_days', 'fine', 'fine_per_day',
        ]
        read_only_fields = [
            'user_name', 'book_title',
            'is_overdue', 'overdue', 'overdue_days', 'fine',
            'actual_return_date', 'fine_per_day',
        ]

    def get_user_name(self, obj):
        try:
            return obj.user.user.get_full_name()
        except Exception:
            return str(obj.user)

    def get_book_title(self, obj):
        return obj.book.title if obj.book else ""

    def get_overdue(self, obj):
        return obj.is_overdue

    def get_fine_per_day(self, obj):
        return 100  # Or dynamically return from settings/config if needed
