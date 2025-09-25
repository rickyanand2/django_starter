# services/services_tenancy.py
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from tenancy.models import Client, Domain

@transaction.atomic
def provision_tenant(*, org_name: str, subdomain: str, plan: str = "standard") -> Client:
    client = Client.objects.create(
        name=org_name,
        schema_name=subdomain,
        plan=plan,
        on_trial=True,
        trial_ends_at=timezone.now() + timedelta(days=14),
    )
    Domain.objects.create(domain=f"{subdomain}.localhost", tenant=client, is_primary=True)
    client.create_schema(check_if_exists=False, sync_schema=True)
    return client
