# tenancy/guards.py
from functools import wraps
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.db import connection
from .models import Membership, Client

def current_client():
    if connection.schema_name == "public":
        return None
    try:
        return Client.objects.get(schema_name=connection.schema_name)
    except Client.DoesNotExist:
        return None

def require_membership(min_role="member"):
    order = {"member": 1, "admin": 2, "owner": 3}

    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            client = current_client()
            if not client:
                return HttpResponseForbidden("No tenant context.")
            try:
                m = Membership.objects.get(user=request.user, client=client, is_active=True)
            except Membership.DoesNotExist:
                return HttpResponseForbidden("No membership for this tenant.")
            if order[m.role] < order[min_role]:
                return HttpResponseForbidden("Insufficient role.")
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
