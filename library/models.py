from django.db import models
from django.utils import timezone
from portalaccount.models import StudentProfile
from datetime import datetime, date


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='books/', blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    isbn = models.CharField("ISBN", max_length=20, unique=True, default="UNKNOWN-ISBN")

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='books')

    author = models.CharField(max_length=255, default="Unknown Author")
    publisher = models.CharField(max_length=100, blank=True, null=True)
    edition = models.CharField(max_length=50, blank=True, null=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    language = models.CharField(max_length=50, default='English')
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.title} by {self.author}"

    def reduce_available_copy(self):
        if self.available_copies > 0:
            self.available_copies -= 1
            self.save()

    def increase_available_copy(self):
        if self.available_copies < self.total_copies:
            self.available_copies += 1
            self.save()


class BorrowedBook(models.Model):
    user = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name='borrowed_books')
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name='borrowed_instances')
    issue_date = models.DateField(default=timezone.now)
    return_date = models.DateField()
    actual_return_date = models.DateField(blank=True, null=True)
    returned = models.BooleanField(default=False)

    class Meta:
        ordering = ['-issue_date']

    def __str__(self):
        return f"{self.user.user.get_full_name()} borrowed {self.book.title}"

    def _parse_date(self, value):
        # Helper to parse string to date if needed
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                return None
        return None

    @property
    def is_overdue(self):
        return_date_obj = self._parse_date(self.return_date)
        if self.returned and self.actual_return_date:
            actual_return_date_obj = self._parse_date(self.actual_return_date)
            if actual_return_date_obj and return_date_obj:
                return actual_return_date_obj > return_date_obj
            return False
        if return_date_obj:
            return timezone.now().date() > return_date_obj
        return False

    @property
    def overdue_days(self):
        return_date_obj = self._parse_date(self.return_date)
        if self.returned and self.actual_return_date:
            actual_return_date_obj = self._parse_date(self.actual_return_date)
            if actual_return_date_obj and return_date_obj:
                delta = actual_return_date_obj - return_date_obj
            else:
                return 0
        else:
            if return_date_obj:
                delta = timezone.now().date() - return_date_obj
            else:
                return 0
        return max(0, delta.days)

    @property
    def fine(self):
        # You can later replace 100 with a dynamic fine per day if you want
        return self.overdue_days * 100

    def mark_as_returned(self):
        self.actual_return_date = timezone.now().date()
        self.returned = True
        self.book.increase_available_copy()
        self.save()
