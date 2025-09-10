# third_party/forms.py

from django import forms
from .models import VendorRequest


class VendorRequestForm(forms.ModelForm):
    class Meta:
        model = VendorRequest
        fields = ["name", "description"]
