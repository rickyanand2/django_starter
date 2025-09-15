# tenancy/views.py
from django.shortcuts import redirect, render
from django.db import connection
from django.contrib.auth.decorators import login_required
from django import forms
from django.contrib import messages
from django.views.generic import FormView
from .models import Client, Domain, Membership

def _is_public():
    return connection.schema_name == "public"

@login_required
def post_login_redirect(request):
    if _is_public():
        m = request.user.memberships.filter(is_active=True).select_related("client").first()
        if not m:
            messages.info(request, "No tenant yet. Create one.")
            return redirect("signup_org")
        d = Domain.objects.filter(tenant=m.client).first()
        return redirect(f"https://{d.domain}/")
    return redirect("/")  # already on tenant → tenant home

def post_logout_redirect(request):
    if _is_public():
        return redirect("public_home")
    return redirect("https://public.localhost:8000/")  # adjust to your public host

class OrgSignupForm(forms.Form):
    org_name = forms.CharField(max_length=200)
    slug = forms.SlugField()
    subdomain = forms.SlugField(help_text="e.g. acme → acme.localhost")

class OrgSignUpView(FormView):
    template_name = "tenancy/signup_org.html"
    form_class = OrgSignupForm

    def form_valid(self, form):
        user = self.request.user
        if not user.is_authenticated:
            messages.error(self.request, "Please sign in first.")
            return redirect("account_login")

        org_name = form.cleaned_data["org_name"]
        slug = form.cleaned_data["slug"]
        subdomain = form.cleaned_data["subdomain"]

        client, created = Client.objects.get_or_create(
            slug=slug,
            defaults={"name": org_name}
        )
        if created:
            client.save()  # creates schema

        Domain.objects.get_or_create(
            domain=f"{subdomain}.localhost:8000",  # dev convenience; use your domain in prod
            tenant=client,
            defaults={"is_primary": True},
        )

        Membership.objects.get_or_create(
            user=user, client=client, defaults={"role": Membership.OWNER}
        )

        messages.success(self.request, "Organisation created.")
        return redirect(f"http://{subdomain}.localhost:8000/")
