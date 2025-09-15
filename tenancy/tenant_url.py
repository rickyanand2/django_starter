# tenancy/tenant_url.py (helper)
# ---------------------------------------------
# filename: tenancy/tenant_url.py
from django.conf import settings
from django_tenants.utils import get_tenant

def urls_for_current_host():
    """
    Returns the correct URLConf dotted path, based on whether we're on public or a tenant.
    django-tenants sets connection.schema_name to 'public' or tenant schema.
    """
    from django.db import connection
    if connection.schema_name == "public":
        return settings.PUBLIC_SCHEMA_URLCONF
    return settings.TENANT_BASE_URLCONF
