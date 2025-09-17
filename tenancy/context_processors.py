# tenancy/context_processors.py
from django.db import connection
from .models import Client

def is_public(request):
    return {"is_public": connection.schema_name == "public"}

def branding(request):
    """
    Very light branding context; safe on public.
    """
    if connection.schema_name == "public":
        return {"brand_color": "#0d6efd", "brand_name": "App"}
    try:
        client = Client.objects.get(schema_name=connection.schema_name)
        return {
            "brand_color": client.brand_color or "#0d6efd",
            "brand_name": client.name or "App",
        }
    except Client.DoesNotExist:
        return {"brand_color": "#0d6efd", "brand_name": "App"}
