from datetime import datetime, time

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Booking, Service
from .scheduling import CLOSED_WEEKDAYS, all_slot_labels, day_slots


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")


class BookingForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    time = forms.ChoiceField(choices=[(t, t) for t in all_slot_labels()], label="Start time")

    class Meta:
        model = Booking
        fields = ["service", "notes"]
        labels = {"notes": "Notes for the barber (optional)"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].queryset = Service.objects.filter(is_active=True)
        self.fields["date"].widget.attrs["min"] = timezone.localdate().isoformat()
        self.order_fields(["service", "date", "time", "notes"])

    def clean_date(self):
        day = self.cleaned_data["date"]
        if day < timezone.localdate():
            raise forms.ValidationError("Choose today or a later date.")
        if day.weekday() in CLOSED_WEEKDAYS:
            raise forms.ValidationError("We are closed on Sundays. Pick another day.")
        return day

    def clean(self):
        data = super().clean()
        service, day, label = data.get("service"), data.get("date"), data.get("time")
        if service and day and label:
            hour, minute = map(int, label.split(":"))
            start = timezone.make_aware(datetime.combine(day, time(hour, minute)))
            if start not in day_slots(day, service.duration_minutes):
                raise forms.ValidationError("That time is not available. Please pick another slot.")
            data["start"] = start
        return data
