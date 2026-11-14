from django.urls import path

from . import api, views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("book/", views.book, name="book"),
    path("my-bookings/", views.my_bookings, name="my_bookings"),
    path("my-bookings/<int:pk>/cancel/", views.cancel_booking, name="cancel_booking"),
    path("staff/", views.dashboard, name="dashboard"),
    path("staff/bookings/<int:pk>/status/", views.update_status, name="update_status"),
    path("staff/services/", views.services_manage, name="services_manage"),
    path("staff/services/new/", views.service_create, name="service_create"),
    path("staff/services/<int:pk>/edit/", views.service_edit, name="service_edit"),
    path("staff/services/<int:pk>/delete/", views.service_delete, name="service_delete"),
    path("api/services/", api.services, name="api_services"),
    path("api/slots/", api.slots, name="api_slots"),
]
