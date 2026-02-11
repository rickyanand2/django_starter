# config/urls_tenants.py
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Your tenant apps:
    path(
        "third-party/",
        include(("third_party.urls", "third_party"), namespace="third_party"),
    ),
    path("accounts/", include("allauth.urls")),  # allauth
    path(
        "",
        RedirectView.as_view(pattern_name="third_party:request_list", permanent=False),
    ),
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    # Default tenant landing:
    path("", RedirectView.as_view(pattern_name="third_party:request_list", permanent=False)),
]

# Optional: keep toolbar for tenant routes too (only in dev)
if getattr(settings, "DEBUG", False) and not getattr(settings, "TESTING", False):
    import debug_toolbar

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
