# accounts/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import ProfileForm
from .models import Profile


@login_required
def settings_home(request):
    return render(request, "accounts/settings.html")


@login_required
def profile_update(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    # Pre-fill email (read-only) and bind to Profile instance
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("accounts:settings")
    else:
        form = ProfileForm(instance=profile)
        # Provide initial email to the disabled field
        form.fields["email"].initial = request.user.email

    return render(request, "accounts/profile_form.html", {"form": form})
