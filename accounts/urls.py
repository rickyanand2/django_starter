# accounts/urls.py
from django.urls import path, include
from . import views

app_name = "accounts"

urlpatterns = [
    # Our settings/profile views
    path("settings/", views.settings_home, name="settings"),
    path("settings/profile/", views.profile_update, name="profile"),
]
