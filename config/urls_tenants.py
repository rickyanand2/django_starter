# config/urls_tenants.py
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from tenancy.views import post_login_redirect, post_logout_redirect

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("post-login/", post_login_redirect, name="post_login"),
    path("post-logout/", post_logout_redirect, name="post_logout"),
    path("", include("third_party.urls")),
    
    path("", include(("third_party.urls", "third_party"), namespace="third_party")),
    # Optional: tenant team management (Phase 3)
    # path("team/invite/", tenancy.views_invites.invite_view, name="tenant_invite"),
]

if getattr(settings, "DEBUG", False) and not getattr(settings, "TESTING", False):
    try:
        import debug_toolbar  # noqa: F401
    except Exception:
        pass
    else:
        urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
