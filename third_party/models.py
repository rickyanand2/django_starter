# third_party/models.py
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

User = get_user_model()


class RequestState(models.TextChoices):
    ONBOARDING = "ONBOARDING", _("Onboarding (Draft)")
    REVIEW = "REVIEW", _("Under review")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")


class VendorRequest(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    state = models.CharField(
        max_length=20, choices=RequestState.choices, default=RequestState.ONBOARDING
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,  # keep nullable to simplify dev
        on_delete=models.SET_NULL,
        related_name="vendor_requests",
    )
    assignee = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="vendor_requests_assigned",
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="vendor_requests_reviewing",
    )

    reject_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} [{self.get_state_display()}]"

    class Meta:
        permissions = [
            ("can_approve_request", "Can approve vendor requests"),
        ]
        verbose_name = "Vendor Request"
