# third_party/urls.py
"""
Purpose: Routes for list/detail/create and state transitions.

Naming: Names are stable, short, and used by templates and redirects.
"""

from django.urls import path

from . import views

app_name = "third_party"

urlpatterns = [
    # Browsing
    path("", views.request_list, name="request_list"),
    path("assigned/", views.request_list_assigned, name="request_list_assigned"),
    path("requests/new/", views.request_create, name="request_create"),
    path("requests/<int:pk>/", views.request_detail, name="request_detail"),
    # Phase shortcuts (nice for sidebar)
    path("requests/draft/", views.request_list_draft, name="request_list_draft"),
    path("requests/review/", views.request_list_review, name="request_list_review"),
    path("requests/approved/", views.request_list_approved, name="request_list_approved"),
    path("requests/rejected/", views.request_list_rejected, name="request_list_rejected"),
    # Transitions
    path("requests/<int:pk>/submit/", views.request_submit, name="request_submit"),
    path("requests/<int:pk>/approve/", views.request_approve, name="request_approve"),
    path("requests/<int:pk>/reject/", views.request_reject, name="request_reject"),
]
