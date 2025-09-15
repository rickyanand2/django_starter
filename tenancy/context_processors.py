from django.db import connection
from django.conf import settings


def branding(request):
    """
    Injects a 'branding' dict into all templates:
      - On tenant hosts: from connection.tenant
      - On public host:   from settings defaults
    Also injects current host name.
    """
    b = {
        "name": getattr(settings, "PUBLIC_SITE_NAME", "VendorGuard"),
        "display_name": getattr(settings, "PUBLIC_SITE_DISPLAY_NAME", "VendorGuard"),
        "primary": getattr(settings, "PUBLIC_BRAND_PRIMARY", "#0d6efd"),
        "secondary": getattr(settings, "PUBLIC_BRAND_SECONDARY", "#6c757d"),
        "logo_url": getattr(settings, "PUBLIC_LOGO_URL", ""),
        "favicon_url": getattr(settings, "PUBLIC_FAVICON_URL", ""),
        "host": request.get_host(),
        "is_public": True,
    }

    tenant = getattr(connection, "tenant", None)
    # When on a tenant host, TenantMainMiddleware sets connection.tenant (schema != public)
    if tenant and getattr(tenant, "schema_name", "public") != "public":
        b.update(
            {
                "name": tenant.name or b["name"],
                "display_name": getattr(tenant, "display_name", "")
                or tenant.name
                or b["display_name"],
                "primary": getattr(tenant, "brand_primary", b["primary"]) or b["primary"],
                "secondary": getattr(tenant, "brand_secondary", b["secondary"]) or b["secondary"],
                "logo_url": tenant.logo.url if getattr(tenant, "logo", None) else b["logo_url"],
                "favicon_url": (
                    tenant.favicon.url if getattr(tenant, "favicon", None) else b["favicon_url"]
                ),
                "is_public": False,
            }
        )
    return {"branding": b}
