from rest_framework import serializers
from .models import Attendance

class AttendanceSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_role = serializers.CharField(source='user.usertype', read_only=True)

    class Meta:
        model = Attendance
        fields = ['id', 'user', 'user_name', 'user_role', 'date', 'status', 'check_in_time', 'check_out_time', 'notes']
