# third_party/signals.py
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_fsm_log.models import StateLog

from .models import ThirdPartyRequest


@receiver(post_save, sender=ThirdPartyRequest)
def log_created_request(sender, instance: ThirdPartyRequest, created, **kwargs):
    """
    Insert a single 'Created' entry into the FSM log.
    KISS: only on initial creation; no transition needed.
    """
    if not created:
        return

    # Optional: skip if someone already inserted a creation log (defensive)
    if StateLog.objects.for_(instance).exists():
        return

    StateLog.objects.create(
        content_type=ContentType.objects.get_for_model(ThirdPartyRequest),
        object_id=instance.pk,
        source_state=None,  # no previous state on creation
        state=instance.state,  # current state (e.g., ONBOARDING)
        by=getattr(instance, "created_by", None),
        description="Created request",
    )
