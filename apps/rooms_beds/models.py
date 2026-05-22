from django.db import models
from hospitals.models import Hospital

class Room(models.Model):
    ROOM_TYPES = [
        ('general-ward', 'General Ward'),
        ('icu', 'ICU'),
        ('private', 'Private Room'),
        ('semi-private', 'Semi-Private Room'),
    ]

    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=50)
    room_type = models.CharField(max_length=50, choices=ROOM_TYPES, default='general-ward')
    charges_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rooms'
        ordering = ['room_number']
        unique_together = ('hospital', 'room_number')

    def __str__(self):
        return f"Room {self.room_number} ({self.get_room_type_display()})"


class Bed(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Under Maintenance'),
    ]

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='beds')
    bed_number = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'beds'
        ordering = ['bed_number']
        unique_together = ('room', 'bed_number')

    def __str__(self):
        return f"Bed {self.bed_number} in Room {self.room.room_number}"
