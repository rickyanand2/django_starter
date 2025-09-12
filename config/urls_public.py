# config/urls_public.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    # Public auth (allauth) — login/signup live on the public host
    path("accounts/", include("allauth.urls")),
    # Public site (landing pages, etc.)
    path("", include("core.urls")),  # core:home etc.
]

# Debug toolbar only when DEBUG and not tests
if getattr(settings, "DEBUG", False) and not getattr(settings, "TESTING", False):
    import debug_toolbar

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
