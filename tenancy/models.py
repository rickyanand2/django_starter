# tenancy/models.py
from django.conf import settings
from django.db import models
from django_tenants.models import DomainMixin, TenantMixin
from django.utils import timezone


class Client(TenantMixin):
    
    name = models.CharField(max_length=200)
    # Unique schema name (identifier)

    user_limit = models.PositiveIntegerField(default=5)
    
    # Client branding (keep it optional for now)

    logo = models.ImageField(upload_to="branding/", blank=True, null=True)
    brand_color = models.CharField(max_length=7, blank=True)  # "#RRGGBB"

    created_on = models.DateTimeField(default=timezone.now)
    # auto create schema on save
    auto_create_schema = True

    def __str__(self):
        return f"{self.name} ({self.schema_name})"


class Domain(DomainMixin):
    # inherits: domain (str), tenant (FK), is_primary (bool)
    pass


class MembershipState(models.TextChoices):
    OWNER = "OWNER", "Owner"
    ADMIN = "ADMIN", "Admin"
    MEMBER = "MEMBER", "Member"
    
    
    
    
    
    

class Membership(models.Model):
    
    # Link to the user (from AUTH_USER_MODEL)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    
    # Links a user to a client with a specific role 
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="memberships")
    
    # Membership state
    role = models.CharField(max_length=10, choices=MembershipState.choices, default=MembershipState.MEMBER)
    
    # Active flag and timestamps
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("user", "client")]

    def __str__(self):
        return f"{self.user} @ {self.client} ({self.role})"