# accounts/forms.py
from django import forms
from django.contrib.auth import get_user_model

from .models import Profile

User = get_user_model()


class ProfileForm(forms.ModelForm):
    email = forms.EmailField(
        disabled=True, required=False, help_text="Manage email under Accounts → Email."
    )

    class Meta:
        model = Profile
        fields = ["job_title", "phone", "country"]
