# tenancy/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.shortcuts import redirect
from django.views.generic import FormView

from .forms import OrgSignupForm
from .services import provision_tenant, get_primary_domain, ensure_owner_membership
from .utils import build_public_url, build_tenant_url

def _is_public() -> bool:
    return connection.schema_name == "public"

@login_required
def post_login_redirect(request):
    if _is_public():
        m = request.user.memberships.filter(is_active=True).select_related("client").first()
        if not m:
            messages.info(request, "No tenant yet. Create one.")
            return redirect("signup_org")
        d = get_primary_domain(m.client)
        return redirect(build_tenant_url(d.domain))
    return redirect("/")

def post_logout_redirect(request):
    if _is_public():
        return redirect("public_home")
    return redirect(build_public_url("/"))

class OrgSignUpView(FormView):
    template_name = "tenancy/signup_org.html"
    form_class = OrgSignupForm

    def form_valid(self, form):
        user = self.request.user
        if not user.is_authenticated:
            messages.error(self.request, "Please sign in first.")
            return redirect("account_login")

        client, domain, _ = provision_tenant(
            org_name=form.cleaned_data["org_name"],
            subdomain=form.cleaned_data["subdomain"],
        )
        ensure_owner_membership(user, client)
        messages.success(self.request, "Organisation created.")
        return redirect(build_tenant_url(domain.domain))
