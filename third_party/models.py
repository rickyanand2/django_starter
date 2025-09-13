# third_party/models.py
"""
Purpose
-------
Domain model + finite-state machine (FSM) for third-party vendor requests.

Why FSM on the model?
- Keeps lifecycle rules close to the data.
- Allows pure, side-effect-free transition methods that are easy to unit test.
- `protected=True` prevents accidental direct state assignment.

Auditing
--------
- Uses django-fsm-log to record every transition (actor + description).
- Admin inline shows the full history.

Testability
-----------
- Transitions are pure methods (`submit_for_review`, `approve`, `reject`) with clear inputs.
- No dependency on request/user inside methods (actor is passed as kwarg).
- Raise precise exceptions for invalid inputs (e.g., missing reject reason).
"""

from django.conf import settings
from django.db import models
from django_fsm import FSMField, transition
from django_fsm_log.decorators import fsm_log_by, fsm_log_description


class RequestState(models.TextChoices):
    """Allowed lifecycle states for ThirdPartyRequest."""

    ONBOARDING = "ONBOARDING", "Draft"
    REVIEW = "REVIEW", "Review"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class ThirdPartyRequest(models.Model):
    """
    A single vendor/third-party onboarding request driven by a simple workflow:
    Draft (ONBOARDING) -> Review (REVIEW) -> Approved (APPROVED)
                         \-> Rejected (REJECTED) from Draft/Review
    """

    # Business fields
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # FSM field (protected = only transitions can change it)
    state = FSMField(
        default=RequestState.ONBOARDING,
        choices=RequestState.choices,
        protected=True,
        help_text="Lifecycle state controlled by model transitions.",
    )

    # Actors
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.PROTECT,
        related_name="requests_assigned",
        help_text="Only the assignee (or staff) may advance or reject.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="requests_created",
        help_text="Request creator; not necessarily the assignee.",
    )

    # Audit extras
    reject_reason = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ---------------- Convenience ----------------

    def is_terminal(self) -> bool:
        """True if no further transitions are possible."""
        return self.state in {RequestState.APPROVED, RequestState.REJECTED}

    # ---------------- Transitions ----------------
    # NOTE: we keep transitions side-effect-free for testability.
    #       Any notifications etc. can be hooked later via signals/services.

    @fsm_log_by  # record "by" user if given
    @fsm_log_description(description="Submitted for review")
    @transition(field=state, source=RequestState.ONBOARDING, target=RequestState.REVIEW)
    def submit_for_review(self, *, by=None, description=None) -> None:
        """Draft -> Review."""
        # (No side effects now; easy to unit test)

    @fsm_log_by
    @fsm_log_description(description="Approved")
    @transition(field=state, source=RequestState.REVIEW, target=RequestState.APPROVED)
    def approve(self, *, by=None, description=None) -> None:
        """Review -> Approved."""
        # (No side effects now; easy to unit test)

    @fsm_log_by
    @fsm_log_description(description="Rejected")
    @transition(
        field=state,
        source=[RequestState.ONBOARDING, RequestState.REVIEW],
        target=RequestState.REJECTED,
    )
    def reject(self, *, reason: str, by=None, description=None) -> None:
        """Draft/Review -> Rejected, requires a non-empty reason."""
        if not reason or not reason.strip():
            # Explicit exception for easy assertion in tests
            raise ValueError("Reject reason is required.")
        self.reject_reason = reason.strip()

    # ---------------- Django extras ----------------
    # template-friendly
    # third_party/models.py  (add inside ThirdPartyRequest)
    # Order used by the UI stepper (and for simple comparisons)
    STEP_ORDER = [RequestState.ONBOARDING, RequestState.REVIEW, RequestState.APPROVED]

    @property
    def state_index(self) -> int:
        """
        Zero-based index of current state in STEP_ORDER.
        Keeps templates dead simple (no custom tags).
        """
        try:
            return self.STEP_ORDER.index(self.state)
        except ValueError:
            # Unknown state: treat as 0 (Draft) for safe render
            return 0

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.name} [{self.get_state_display()}]"
