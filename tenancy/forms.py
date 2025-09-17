# tenancy/forms.py
from django import forms

class OrgSignupForm(forms.Form):
    org_name = forms.CharField(
        max_length=200,
        label="Organisation name"
    )
    subdomain = forms.SlugField(
        help_text="e.g. acme → acme.localhost:8000"
    )
