from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.http import Http404, FileResponse
from django.shortcuts import get_object_or_404
from .models import Announcement
from .serializers import AnnouncementSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication


class AnnouncementListCreate(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        category = request.query_params.get('category')
        user_id = request.query_params.get('user_id')

        announcements = Announcement.objects.all()  # Removed filter(is_active=True)
        print(f"[DEBUG] Initial announcements count: {announcements.count()}")

        if category:
            announcements = announcements.filter(category=category)
            print(f"[DEBUG] Filtered by category='{category}': {announcements.count()}")

        if user_id:
            try:
                user_id = int(user_id)
                announcements = announcements.filter(posted_by__id=user_id)
                print(f"[DEBUG] Filtered by user_id={user_id}: {announcements.count()}")
            except ValueError:
                print(f"[ERROR] Invalid user_id={user_id} (not an integer)")

        serializer = AnnouncementSerializer(announcements, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        print(f"[DEBUG] POST data: {request.data}")
        serializer = AnnouncementSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(posted_by=request.user)
            print("[DEBUG] Announcement created")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(f"[ERROR] Validation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AnnouncementDetail(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        try:
            return Announcement.objects.get(pk=pk)
        except Announcement.DoesNotExist:
            print(f"[ERROR] Announcement with ID={pk} not found")
            raise Http404

    def get(self, request, pk):
        announcement = self.get_object(pk)
        serializer = AnnouncementSerializer(announcement, context={'request': request})
        return Response(serializer.data)

    def put(self, request, pk):
        announcement = self.get_object(pk)
        if request.user != announcement.posted_by and not request.user.is_staff:
            print(f"[ERROR] Unauthorized PUT by {request.user}")
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        print(f"[DEBUG] PUT data: {request.data}")
        serializer = AnnouncementSerializer(announcement, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save(posted_by=request.user)
            print("[DEBUG] Announcement updated")
            return Response(serializer.data)
        print(f"[ERROR] Update failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        announcement = self.get_object(pk)
        if request.user != announcement.posted_by and not request.user.is_staff:
            print(f"[ERROR] Unauthorized DELETE by {request.user}")
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        print(f"[DEBUG] Deleting announcement ID={pk}")
        announcement.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AnnouncementFileDownload(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        try:
            announcement = Announcement.objects.get(pk=pk)
            print(f"[DEBUG] Found announcement ID={pk}")
        except Announcement.DoesNotExist:
            print(f"[ERROR] Announcement ID={pk} not found")
            raise Http404("Announcement not found")

        if not announcement.file:
            print(f"[ERROR] No file for announcement ID={pk}")
            return Response({"detail": "No file attached."}, status=404)

        try:
            file_handle = announcement.file.open('rb')
            filename = announcement.file.name.split("/")[-1]
            print(f"[DEBUG] Sending file '{filename}'")
            return FileResponse(file_handle, as_attachment=True, filename=filename)
        except Exception as e:
            print(f"[ERROR] File open/download failed: {str(e)}")
            return Response({"detail": "File error."}, status=500)
