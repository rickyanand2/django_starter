# accounts/adapters.py
from allauth.account.adapter import DefaultAccountAdapter
from django.core.exceptions import ValidationError

FREE = {"gmail.com","yahoo.com","outlook.com","hotmail.com","icloud.com","proton.me","aol.com"}

class AccountAdapter(DefaultAccountAdapter):
    def clean_email(self, email):
        email = super().clean_email(email)
        domain = email.split("@")[-1].lower()
        if domain in FREE:
            raise ValidationError("Please use your corporate email address.")
        return email
