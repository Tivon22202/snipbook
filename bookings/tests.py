from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Booking, Service
from .scheduling import CLOSED_WEEKDAYS


class BookingTests(TestCase):
    def setUp(self):
        self.amina = User.objects.create_user("amina", password="pw-12345-xyz")
        self.bob = User.objects.create_user("bob", password="pw-12345-xyz")
        self.service = Service.objects.create(name="Haircut", duration_minutes=30, price=Decimal("500"))
        day = timezone.localdate() + timedelta(days=2)
        while day.weekday() in CLOSED_WEEKDAYS:
            day += timedelta(days=1)
        self.day = day

    def make(self, user, hour=10, minute=0):
        start = timezone.make_aware(datetime.combine(self.day, time(hour, minute)))
        return Booking.objects.create(customer=user, service=self.service, start=start)

    def payload(self, label="10:00"):
        return {"service": self.service.pk, "date": self.day.isoformat(), "time": label, "notes": ""}

    def test_end_time_is_computed(self):
        booking = self.make(self.amina)
        self.assertEqual(booking.end - booking.start, timedelta(minutes=30))

    def test_booking_requires_login(self):
        response = self.client.get(reverse("book"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_can_book_a_free_slot(self):
        self.client.login(username="amina", password="pw-12345-xyz")
        response = self.client.post(reverse("book"), self.payload())
        self.assertRedirects(response, reverse("my_bookings"))
        self.assertEqual(Booking.objects.filter(customer=self.amina).count(), 1)

    def test_double_booking_is_rejected(self):
        self.make(self.bob, 10, 0)
        self.client.login(username="amina", password="pw-12345-xyz")
        response = self.client.post(reverse("book"), self.payload("10:00"))
        self.assertEqual(response.status_code, 200)  # form shown again with an error
        self.assertEqual(Booking.objects.count(), 1)

    def test_cannot_cancel_someone_elses_booking(self):
        booking = self.make(self.bob)
        self.client.login(username="amina", password="pw-12345-xyz")
        response = self.client.post(reverse("cancel_booking", args=[booking.pk]))
        self.assertEqual(response.status_code, 404)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.PENDING)

    def test_owner_can_cancel(self):
        booking = self.make(self.amina)
        self.client.login(username="amina", password="pw-12345-xyz")
        self.client.post(reverse("cancel_booking", args=[booking.pk]))
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.CANCELLED)

    def test_dashboard_is_staff_only(self):
        self.client.login(username="amina", password="pw-12345-xyz")
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 403)
        User.objects.create_user("owner", password="pw-12345-xyz", is_staff=True)
        self.client.login(username="owner", password="pw-12345-xyz")
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)

    def test_slots_api_hides_taken_times(self):
        self.make(self.bob, 10, 0)
        response = self.client.get(reverse("api_slots"), {"date": self.day.isoformat(), "service": self.service.pk})
        slots = response.json()["slots"]
        self.assertNotIn("10:00", slots)
        self.assertIn("10:30", slots)

    def test_slots_api_validates_input(self):
        response = self.client.get(reverse("api_slots"), {"date": "nonsense", "service": "x"})
        self.assertEqual(response.status_code, 400)
