from django.contrib import admin

from .models import Booking, Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "duration_minutes", "price", "is_active")
    list_filter = ("is_active",)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("customer", "service", "start", "status")
    list_filter = ("status", "service")
    date_hierarchy = "start"
