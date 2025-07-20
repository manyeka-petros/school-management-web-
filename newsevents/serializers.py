from rest_framework import serializers
from .models import Announcement

class AnnouncementSerializer(serializers.ModelSerializer):
    posted_by_username = serializers.ReadOnlyField(source='posted_by.username')
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Announcement
        fields = [
            'id', 'title', 'content', 'category', 'posted_by', 'posted_by_username',
            'posted_at', 'file', 'file_url'
        ]

    def get_file_url(self, obj):
        """
        Returns the absolute URL of the file if available.
        """
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url') and request:
            return request.build_absolute_uri(obj.file.url)
        return None
