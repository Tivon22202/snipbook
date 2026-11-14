"""Small JSON API. The booking page calls /api/slots/ to show only free times."""
from datetime import date

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

from .models import Service
from .scheduling import day_slots


@require_GET
def services(request):
    data = [
        {"id": s.id, "name": s.name, "description": s.description,
         "duration_minutes": s.duration_minutes, "price": str(s.price)}
        for s in Service.objects.filter(is_active=True)
    ]
    return JsonResponse({"services": data})


@require_GET
def slots(request):
    try:
        day = date.fromisoformat(request.GET["date"])
        service = Service.objects.get(pk=int(request.GET["service"]), is_active=True)
    except (KeyError, ValueError, Service.DoesNotExist):
        return JsonResponse({"error": "Provide a valid date (YYYY-MM-DD) and an active service id."}, status=400)
    free = [timezone.localtime(s).strftime("%H:%M") for s in day_slots(day, service.duration_minutes)]
    return JsonResponse({"date": day.isoformat(), "service": service.id, "slots": free})
