from django.conf import settings


def shop(request):
    return {"SHOP_NAME": settings.SHOP_NAME, "CURRENCY": settings.CURRENCY}
