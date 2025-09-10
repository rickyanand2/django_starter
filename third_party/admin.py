# third_party/admin.py
from django.contrib import admin
from .models import VendorRequest


@admin.register(VendorRequest)
class VendorRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "state", "created_by", "reviewer", "created_at")
    list_filter = ("state", "created_by", "reviewer", "created_at")
    search_fields = ("name", "description")
    readonly_fields = ("state", "created_at", "updated_at", "reject_reason")
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_staff:
            return qs
        return qs.filter(created_by=request.user)

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_staff:
            return self.readonly_fields
        return self.readonly_fields + ("created_by", "assignee", "reviewer")
