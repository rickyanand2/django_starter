from django.contrib import admin
from django_tenants.admin import TenantAdminMixin

from .models import Client, Domain, Membership


@admin.register(Client)
class ClientAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ("name", "schema_name", "user_limit")
    search_fields = ("name", "schema_name")
    
    list_filter = ("created_on",)


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ("domain", "tenant", "is_primary")
    search_fields = ("domain", "tenant__name")

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "client", "role", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("user__email", "client__name")