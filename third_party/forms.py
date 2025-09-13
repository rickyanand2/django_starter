# third_party/forms.py
"""
Purpose
-------
Form wrapper for ThirdPartyRequest creation/editing.

KISS choices:
- Only expose the fields we actually want users to set.
- Enforce 'assignee' requirement at the form level for early feedback.

Testability
-----------
- Validate 'assignee' required.
- Ensure widget types and labels are set as expected.
"""

from django import forms
from .models import ThirdPartyRequest


class ThirdPartyRequestForm(forms.ModelForm):
    class Meta:
        model = ThirdPartyRequest
        fields = ["name", "description", "assignee"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "assignee": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assignee"].required = True
        # Add 'is-invalid' class dynamically when errors exist (for Bootstrap feedback)
        for name, field in self.fields.items():
            if self.errors.get(name):
                css = field.widget.attrs.get("class", "")
                field.widget.attrs["class"] = (css + " is-invalid").strip()
        # Optional: predictable ordering
        qs = self.fields["assignee"].queryset
        self.fields["assignee"].queryset = qs.order_by(
            "first_name", "last_name", "email"
        )
