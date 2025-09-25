# tenancy/models.py
from django.conf import settings
from django.db import models
from django_tenants.models import DomainMixin, TenantMixin
from django.utils import timezone


PLAN_CHOICES = [
    ("standard", "Standard"),
    ("teams", "Teams"),
    ("enterprise", "Enterprise"),
]


class Client(TenantMixin):
    
    name = models.CharField(max_length=200)
    plan = models.CharField(max_length=16, choices=PLAN_CHOICES, default="standard")
    user_limit = models.PositiveIntegerField(default=5)
    paid_until = models.DateField(null=True, blank=True)
    on_trial = models.BooleanField(default=False)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    
    # Client branding (keep it optional for now)
    logo = models.ImageField(upload_to="branding/", blank=True, null=True)
    brand_color = models.CharField(max_length=7, blank=True)  # "#RRGGBB"
    created_on = models.DateTimeField(default=timezone.now)    
    
    auto_create_schema = True # django-tenants flag

    def trial_active(self) -> bool:
        return bool(self.on_trial and self.trial_ends_at and self.trial_ends_at > timezone.now())

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