# accounts/urls.py
from django.urls import path, include
from . import views

app_name = "accounts"

urlpatterns = [
    # allauth routes remain:
    path("", include("allauth.urls")),
    # our settings hub:
    path("settings/", views.settings_home, name="settings"),
    path("settings/profile/", views.profile_update, name="profile"),
]

# Note: The login and logout routes are provided by allauth and do not need to be explicitly defined here.
