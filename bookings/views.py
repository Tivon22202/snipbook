from datetime import date
from functools import wraps

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import BookingForm, RegisterForm
from .models import Booking, Service
from .scheduling import day_slots


def staff_required(view):
    """Logged-in staff only. Logged-in non-staff get a 403 instead of a redirect loop."""
    @login_required
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapper


def home(request):
    return render(request, "bookings/home.html", {"services": Service.objects.filter(is_active=True)})


def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Welcome! Your account is ready.")
        return redirect("my_bookings")
    return render(request, "registration/register.html", {"form": form})


@login_required
def book(request):
    initial = {"service": request.GET["service"]} if request.GET.get("service", "").isdigit() else {}
    form = BookingForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        start = form.cleaned_data["start"]
        service = form.cleaned_data["service"]
        with transaction.atomic():
            # Re-check inside the transaction so two people can't take the same slot.
            if start in day_slots(start.date(), service.duration_minutes):
                booking = form.save(commit=False)
                booking.customer, booking.start = request.user, start
                booking.save()
                messages.success(request, f"Booked: {service.name} on {timezone.localtime(start):%a %d %b at %H:%M}.")
                return redirect("my_bookings")
        form.add_error(None, "Someone just took that slot. Please pick another time.")
    return render(request, "bookings/book.html", {"form": form})


@login_required
def my_bookings(request):
    now = timezone.now()
    mine = request.user.bookings.select_related("service")
    return render(request, "bookings/my_bookings.html", {
        "upcoming": mine.filter(start__gte=now).exclude(status=Booking.CANCELLED),
        "past": mine.filter(Q(start__lt=now) | Q(status=Booking.CANCELLED)).order_by("-start"),
    })


@login_required
@require_POST
def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk, customer=request.user)  # owners only
    if booking.can_cancel:
        booking.status = Booking.CANCELLED
        booking.save()
        messages.success(request, "Booking cancelled.")
    else:
        messages.error(request, "This booking can no longer be cancelled.")
    return redirect("my_bookings")


@staff_required
def dashboard(request):
    qs = Booking.objects.select_related("service", "customer")
    status = request.GET.get("status", "")
    day = request.GET.get("date", "")
    if status in dict(Booking.STATUS_CHOICES):
        qs = qs.filter(status=status)
    try:
        if day:
            qs = qs.filter(start__date=date.fromisoformat(day))
        else:
            qs = qs.filter(start__gte=timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0))
    except ValueError:
        messages.error(request, "Use a valid date.")
    today = timezone.localdate()
    stats = {
        "today": Booking.objects.filter(start__date=today).exclude(status=Booking.CANCELLED).count(),
        "pending": Booking.objects.filter(status=Booking.PENDING, start__gte=timezone.now()).count(),
        "customers": Booking.objects.values("customer").distinct().count(),
    }
    return render(request, "bookings/dashboard.html", {
        "bookings": qs, "stats": stats, "status": status, "day": day,
        "statuses": Booking.STATUS_CHOICES,
    })


@staff_required
@require_POST
def update_status(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    new = request.POST.get("status")
    if new in dict(Booking.STATUS_CHOICES):
        booking.status = new
        booking.save()
        messages.success(request, f"Booking marked {booking.get_status_display().lower()}.")
    return redirect("dashboard")


@staff_required
def services_manage(request):
    return render(request, "bookings/services_manage.html", {"services": Service.objects.all()})


def _service_form():
    from django import forms

    class ServiceForm(forms.ModelForm):
        class Meta:
            model = Service
            fields = ["name", "description", "duration_minutes", "price", "is_active"]

        def clean_duration_minutes(self):
            minutes = self.cleaned_data["duration_minutes"]
            if minutes < 15 or minutes % 15:
                raise forms.ValidationError("Use a multiple of 15 minutes, at least 15.")
            return minutes
    return ServiceForm


@staff_required
def service_create(request):
    form = _service_form()(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Service added.")
        return redirect("services_manage")
    return render(request, "bookings/service_form.html", {"form": form, "title": "Add service"})


@staff_required
def service_edit(request, pk):
    service = get_object_or_404(Service, pk=pk)
    form = _service_form()(request.POST or None, instance=service)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Service updated.")
        return redirect("services_manage")
    return render(request, "bookings/service_form.html", {"form": form, "title": f"Edit {service.name}"})


@staff_required
@require_POST
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    try:
        service.delete()
        messages.success(request, "Service deleted.")
    except ProtectedError:
        messages.error(request, "This service has bookings, so it can't be deleted. Hide it instead by editing it.")
    return redirect("services_manage")
