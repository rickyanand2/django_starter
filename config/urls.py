# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
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
