"""
Schedule Models
Maps the PHP 'schedule' table to Django ORM
"""
from django.db import models
from doctors.models import Doctor


class Schedule(models.Model):
    """
    Doctor schedule/session.
    Corresponds to PHP 'schedule' table.
    """
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    title = models.CharField(max_length=255)
    schedule_date = models.DateField()
    schedule_time = models.TimeField()
    max_patients = models.PositiveIntegerField(
        default=50,
        help_text='Maximum number of appointments for this session'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'schedule'
        ordering = ['-schedule_date', '-schedule_time']

    def __str__(self):
        return f"{self.title} - {self.doctor.name} on {self.schedule_date}"

    @property
    def booked_count(self):
        """Number of confirmed appointments for this session."""
        return self.appointments.count()

    @property
    def available_slots(self):
        """Remaining slots. Returns 0 if doctor is absent/on leave."""
        if self.doctor.user:
            from common.models import Attendance
            if Attendance.objects.filter(user=self.doctor.user, date=self.schedule_date, status__in=['ABSENT', 'LEAVE']).exists():
                return 0
        from doctors.models import LeaveRequest
        if LeaveRequest.objects.filter(doctor=self.doctor, start_date__lte=self.schedule_date, end_date__gte=self.schedule_date, status='APPROVED').exists():
            return 0
        return max(0, self.max_patients - self.booked_count)

    @property
    def is_full(self):
        return self.available_slots == 0


class Shift(models.Model):
    hospital = models.ForeignKey(
        'hospitals.Hospital',
        on_delete=models.CASCADE,
        related_name='shifts'
    )
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shift'
        unique_together = [['hospital', 'name']]
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"

