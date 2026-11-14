from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Service(models.Model):
    name = models.CharField(max_length=80, unique=True)
    description = models.CharField(max_length=200, blank=True)
    duration_minutes = models.PositiveIntegerField(help_text="Length of the appointment in minutes.")
    price = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True, help_text="Untick to hide from customers.")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Booking(models.Model):
    PENDING, CONFIRMED, COMPLETED, CANCELLED = "pending", "confirmed", "completed", "cancelled"
    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (CONFIRMED, "Confirmed"),
        (COMPLETED, "Completed"),
        (CANCELLED, "Cancelled"),
    ]
    ACTIVE_STATUSES = (PENDING, CONFIRMED)  # these block the calendar

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name="bookings")
    start = models.DateTimeField(db_index=True)
    end = models.DateTimeField(editable=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    notes = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start"]

    def __str__(self):
        return f"{self.service} for {self.customer} at {self.start:%Y-%m-%d %H:%M}"

    def save(self, *args, **kwargs):
        self.end = self.start + timedelta(minutes=self.service.duration_minutes)
        super().save(*args, **kwargs)

    @property
    def can_cancel(self):
        return self.status in self.ACTIVE_STATUSES and self.start > timezone.now()
