# accounts/views.py
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import ProfileForm


@login_required
def settings_home(request):
    return render(request, "accounts/settings.html")


@login_required
def profile_update(request):
    form = ProfileForm(instance=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("settings")
    return render(request, "accounts/profile_form.html", {"form": form})
