from django.db import models
from django.utils import timezone
from authentication.models import WebUser

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LEAVE', 'On Leave'),
        ('HALF_DAY', 'Half Day')
    ]
    
    user = models.ForeignKey(WebUser, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PRESENT')
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'attendance'
        unique_together = [['user', 'date']]
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.name} - {self.date} ({self.status})"
