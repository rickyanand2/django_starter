# config/urls_public.py
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from tenancy.views import post_login_redirect, post_logout_redirect, OrgSignUpView


urlpatterns = [
    path("admin/", admin.site.urls),    
    path("accounts/", include("allauth.urls")), # Public auth (allauth) — login/signup live on the public host
    path("post-login/", post_login_redirect, name="post_login"),
    path("post-logout/", post_logout_redirect, name="post_logout"),
    path("signup-org/", OrgSignUpView.as_view(), name="signup_org"),    
    path("", include("core.urls")),  # core:home etc. # Public site (landing pages, etc.)
]

# Debug toolbar only when DEBUG and not tests
if getattr(settings, "DEBUG", False) and not getattr(settings, "TESTING", False):
    import debug_toolbar
    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
