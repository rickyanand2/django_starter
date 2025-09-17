# third_party/urls.py
from django.urls import path
from . import views

app_name = "third_party"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("requests/", views.request_list, name="request_list"),
    path("assigned/", views.request_list_assigned, name="request_list_assigned"),
    path("requests/new/", views.request_create, name="request_create"),
    path("requests/<int:pk>/", views.request_detail, name="request_detail"),

    path("requests/draft/", views.request_list_draft, name="request_list_draft"),
    path("requests/review/", views.request_list_review, name="request_list_review"),
    path("requests/approved/", views.request_list_approved, name="request_list_approved"),
    path("requests/rejected/", views.request_list_rejected, name="request_list_rejected"),

    path("requests/<int:pk>/submit/", views.request_submit, name="request_submit"),
    path("requests/<int:pk>/approve/", views.request_approve, name="request_approve"),
    path("requests/<int:pk>/reject/", views.request_reject, name="request_reject"),
]
