# tenancy/services.py
from django.core.exceptions import ValidationError
from .models import Client, Domain, Membership, MembershipState
from .utils import normalize_schema_name, make_tenant_domain

def get_primary_domain(client: Client) -> Domain:
    dom = Domain.objects.filter(tenant=client, is_primary=True).first()
    if dom:
        return dom
    dom = Domain.objects.filter(tenant=client).first()
    if not dom:
        raise ValidationError("No domain configured for tenant.")
    return dom

def ensure_owner_membership(user, client: Client) -> Membership:
    m, _ = Membership.objects.get_or_create(
        user=user,
        client=client,
        defaults={"role": MembershipState.OWNER},
    )
    return m

def provision_tenant(*, org_name: str, subdomain: str) -> tuple[Client, Domain, bool]:
    """
    Create or reuse a tenant for subdomain. Returns (client, domain, created_client).
    Ensures: no port in Domain.domain.
    """
    schema = normalize_schema_name(subdomain)
    client, created = Client.objects.get_or_create(
        schema_name=schema,
        defaults={"name": org_name},
    )
    if created:
        client.save()  # auto_create_schema -> create schema
    bare_domain = make_tenant_domain(subdomain)
    domain, _ = Domain.objects.get_or_create(
        domain=bare_domain,
        tenant=client,
        defaults={"is_primary": True},
    )
    return client, domain, created
