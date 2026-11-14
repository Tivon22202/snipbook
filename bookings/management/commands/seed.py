import os
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from bookings.models import Service

SERVICES = [
    ("Classic haircut", "Scissor or clipper cut, finished with a neck shave.", 30, "500"),
    ("Beard trim", "Shape and line-up with a hot towel.", 30, "300"),
    ("Cut and beard", "The full haircut plus beard trim.", 60, "750"),
    ("Kids' cut", "For children under 12.", 30, "350"),
    ("Hair colour", "Single-colour treatment, includes wash.", 90, "1500"),
]


class Command(BaseCommand):
    help = "Create sample services and a staff account for development."

    def handle(self, *args, **options):
        for name, desc, minutes, price in SERVICES:
            Service.objects.get_or_create(name=name, defaults={
                "description": desc, "duration_minutes": minutes, "price": Decimal(price)})
        password = os.environ.get("SEED_STAFF_PASSWORD", "ChangeMe-dev-123")
        staff, created = User.objects.get_or_create(username="owner", defaults={
            "is_staff": True, "is_superuser": True, "email": "owner@example.com"})
        if created:
            staff.set_password(password)
            staff.save()
        self.stdout.write(self.style.SUCCESS(
            "Seeded services. Staff login: owner / " + (password if created else "(existing password)")))
