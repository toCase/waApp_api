from django.db import models
from django.conf import settings

class Staff(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True)
    title = models.CharField(max_length=255)
    position = models.CharField(max_length=255, blank=True)
    link = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    bg_color = models.CharField(max_length=9, default="#FFFFFF")
    fg_color = models.CharField(max_length=9, default="#000000")
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title

class ScheduleTemplate(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title

class TemplateInterval(models.Model):
    schedule = models.ForeignKey(ScheduleTemplate, on_delete=models.CASCADE, related_name="intervals")
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_size = models.PositiveSmallIntegerField()

class WorkSlot(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.PROTECT, null=True)
    work_day = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    template = models.ForeignKey(ScheduleTemplate, on_delete=models.PROTECT, null=True)
    is_blocked = models.BooleanField(default=False)
    blocked_by = models.ForeignKey(
        'Appointment',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="blocked_slots"
    )

class Appointment(models.Model):
    slot = models.OneToOneField(WorkSlot, on_delete=models.CASCADE, related_name="appointment")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True)
    notes = models.TextField(blank=True)
    status = models.PositiveSmallIntegerField(default=0)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)