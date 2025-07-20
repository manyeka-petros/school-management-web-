from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.db import IntegrityError

from .models import Attendance
from .serializers import AttendanceSerializer


class AttendanceListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        List attendance records. Optional query params:
        - user_type (e.g., student, teacher, staff)
        - date
        - classroom (id)
        """
        user_type = request.query_params.get('user_type')
        date_str = request.query_params.get('date')
        classroom = request.query_params.get('classroom')

        queryset = Attendance.objects.all()

        if user_type:
            queryset = queryset.filter(user__user_type=user_type)

        if date_str:
            parsed_date = parse_date(date_str)
            if parsed_date:
                queryset = queryset.filter(date=parsed_date)

        if classroom:
            queryset = queryset.filter(classroom_id=classroom)

        serializer = AttendanceSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Record attendance. Requires user ID, status, classroom ID, and optional date.
        """
        serializer = AttendanceSerializer(data=request.data)

        if serializer.is_valid():
            try:
                attendance = serializer.save()
                return Response(AttendanceSerializer(attendance).data, status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response(
                    {"detail": "Attendance for this user on this date already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                print("Error saving attendance:", e)
                return Response(
                    {"detail": "Internal server error saving attendance."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        # If serializer is not valid
        print("Validation errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
