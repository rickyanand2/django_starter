# config/urls.py
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # Keep Allauth names like 'account_login' available (what your templates/tests use)
    path("accounts/", include("allauth.urls")),
    # Your app-specific views (namespaced as 'accounts:settings', 'accounts:profile', etc.)
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("", include("core.urls")),
    path(
        "third-party/",
        include(("third_party.urls", "third_party"), namespace="third_party"),
    ),
]

# Only mount toolbar when DEBUG and not running tests
if getattr(settings, "DEBUG", False) and not getattr(settings, "TESTING", False):
    import debug_toolbar

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
