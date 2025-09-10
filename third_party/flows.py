# third_party/flows.py
from django.db import transaction
from viewflow.fsm import State
from .models import VendorRequest, RequestState


class VendorRequestFlow:
    # State is a descriptor that reads/writes via the getter/setter below
    state = State(RequestState, default=RequestState.ONBOARDING)

    def __init__(self, obj: VendorRequest):
        self.obj = obj

    # Wire the descriptor to your model field
    @state.getter()
    def get_state(self):
        return self.obj.state

    @state.setter()
    def set_state(self, value):
        self.obj.state = value

    # After a successful transition, persist changes
    @state.on_success()
    def save_on_success(self, *_args, **_kwargs):
        with transaction.atomic():
            self.obj.save(update_fields=["state", "reject_reason", "updated_at"])

    # Transitions
    @state.transition(source=RequestState.ONBOARDING, target=RequestState.REVIEW)
    def submit_for_review(self, by_user):
        # keep pure; permissions are enforced in the view
        pass

    @state.transition(source=RequestState.REVIEW, target=RequestState.APPROVED)
    def approve(self, by_user):
        pass

    @state.transition(source=RequestState.REVIEW, target=RequestState.REJECTED)
    def reject(self, by_user, reason: str = ""):
        self.obj.reject_reason = reason
