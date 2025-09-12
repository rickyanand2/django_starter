# core/models.py
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin


class Client(TenantMixin):
    name = models.CharField(max_length=200)
    on_trial = models.BooleanField(default=True)
    created_on = models.DateField(auto_now_add=True)

    # auto create schema on save
    auto_create_schema = True

    def __str__(self):
        return f"{self.name} ({self.schema_name})"


class Domain(DomainMixin):
    # inherits: domain (str), tenant (FK), is_primary (bool)
    def __str__(self):
        return self.domain
