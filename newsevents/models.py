from django.db import models
from django.conf import settings


class Announcement(models.Model):
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('promotion', 'Promotion'),
        ('event', 'Event'),
        ('update', 'Update'),
    ]

    title = models.CharField(max_length=255)
    content = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='announcements'
    )
    posted_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='announcements/', blank=True, null=True)

    class Meta:
        ordering = ['-posted_at']

    def __str__(self):
        return f"{self.title} ({self.category})"
