"""Opening hours and availability. The shop has one chair, so bookings cannot overlap."""
from datetime import datetime, time, timedelta

from django.utils import timezone

from .models import Booking

OPEN = time(9, 0)
CLOSE = time(18, 0)
STEP_MINUTES = 30
CLOSED_WEEKDAYS = {6}  # Sunday


def all_slot_labels():
    """Every start time the shop could offer, as 'HH:MM' strings."""
    labels, cur = [], datetime.combine(datetime.today(), OPEN)
    end = datetime.combine(datetime.today(), CLOSE)
    while cur < end:
        labels.append(cur.strftime("%H:%M"))
        cur += timedelta(minutes=STEP_MINUTES)
    return labels


def day_slots(day, duration_minutes):
    """Free, future start times (aware datetimes) on `day` for an appointment of this length."""
    if day.weekday() in CLOSED_WEEKDAYS:
        return []
    tz = timezone.get_current_timezone()
    open_dt = timezone.make_aware(datetime.combine(day, OPEN), tz)
    close_dt = timezone.make_aware(datetime.combine(day, CLOSE), tz)
    busy = list(
        Booking.objects.filter(status__in=Booking.ACTIVE_STATUSES, start__lt=close_dt, end__gt=open_dt)
        .values_list("start", "end")
    )
    now, length = timezone.now(), timedelta(minutes=duration_minutes)
    slots, cur = [], open_dt
    while cur + length <= close_dt:
        end = cur + length
        if cur > now and not any(s < end and e > cur for s, e in busy):
            slots.append(cur)
        cur += timedelta(minutes=STEP_MINUTES)
    return slots
