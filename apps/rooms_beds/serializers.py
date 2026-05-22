from rest_framework import serializers
from .models import Room, Bed

class RoomSerializer(serializers.ModelSerializer):
    beds_count = serializers.IntegerField(source='beds.count', read_only=True)
    available_beds_count = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ['id', 'room_number', 'room_type', 'charges_per_day', 'beds_count', 'available_beds_count', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_available_beds_count(self, obj):
        return obj.beds.filter(status='available').count()


class BedSerializer(serializers.ModelSerializer):
    room_number = serializers.CharField(source='room.room_number', read_only=True)
    room_type = serializers.CharField(source='room.room_type', read_only=True)
    charges_per_day = serializers.DecimalField(source='room.charges_per_day', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Bed
        fields = ['id', 'room', 'room_number', 'room_type', 'charges_per_day', 'bed_number', 'status', 'created_at']
        read_only_fields = ['id', 'created_at']
