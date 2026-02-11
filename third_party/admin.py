# third_party/admin.py
"""
Purpose
-------
Admin visibility with inlined transition history (django-fsm-log).

Testability
-----------
- Admin loads with the inline attached.
"""

from django.contrib import admin
from django_fsm_log.admin import StateLogInline

from .models import ThirdPartyRequest


@admin.register(ThirdPartyRequest)
class ThirdPartyRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "assignee", "state", "created_at")
    list_filter = ("state",)
    search_fields = ("name", "description", "assignee__email", "created_by__email")
    readonly_fields = ("state", "reject_reason", "created_at", "updated_at")
    inlines = [StateLogInline]
