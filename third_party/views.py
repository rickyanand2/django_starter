# third_party/views.py
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.http import HttpResponse, HttpResponseBadRequest
from django.template.loader import render_to_string

from viewflow.fsm import TransitionNotAllowed

from .models import VendorRequest, RequestState
from .forms import VendorRequestForm
from .flows import VendorRequestFlow


def _is_owner_or_staff(user, obj):
    return user.is_staff or user == obj.created_by


@login_required
def request_list(request):
    qs = VendorRequest.objects.order_by("-pk")
    if not request.user.is_staff:
        qs = qs.filter(created_by=request.user)

    paginator = Paginator(qs, 20)
    page = request.GET.get("page")
    page_obj = paginator.get_page(page)

    return render(
        request,
        "third_party/request_list.html",
        {
            "objects": page_obj.object_list,  # keep template compatibility
            "page_obj": page_obj,
            "paginator": paginator,
        },
    )


@login_required
def request_detail(request, pk: int):
    obj = get_object_or_404(VendorRequest, pk=pk)
    if not _is_owner_or_staff(request.user, obj):
        raise PermissionDenied

    return render(
        request,
        "third_party/request_detail.html",
        {
            "obj": obj,
            # Expose enum for template comparisons like RequestState.ONBOARDING
            "RequestState": RequestState,
        },
    )


@login_required
def request_create(request):
    if request.method == "POST":
        form = VendorRequestForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
            return redirect("third_party:request_detail", pk=obj.pk)
    else:
        form = VendorRequestForm()

    return render(request, "third_party/request_form.html", {"form": form})


# -------- Transitions (HTMX + PRG) --------


@login_required
@require_POST
def request_submit(request, pk: int):
    obj = get_object_or_404(VendorRequest, pk=pk)
    if not _is_owner_or_staff(request.user, obj):
        raise PermissionDenied

    flow = VendorRequestFlow(obj)
    try:
        flow.submit_for_review(request.user)
    except TransitionNotAllowed:
        return HttpResponseBadRequest("Transition not allowed from current state")

    if request.headers.get("HX-Request") == "true":
        html = render_to_string(
            "third_party/partials/request_row.html", {"obj": obj}, request
        )
        return HttpResponse(html)
    return redirect("third_party:request_detail", pk=obj.pk)


@login_required
@require_POST
def request_approve(request, pk: int):
    obj = get_object_or_404(VendorRequest, pk=pk)
    if not request.user.is_staff:
        raise PermissionDenied

    flow = VendorRequestFlow(obj)
    try:
        flow.approve(request.user)
    except TransitionNotAllowed:
        return HttpResponseBadRequest("Transition not allowed from current state")

    if request.headers.get("HX-Request") == "true":
        html = render_to_string(
            "third_party/partials/request_row.html", {"obj": obj}, request
        )
        return HttpResponse(html)
    return redirect("third_party:request_detail", pk=obj.pk)


@login_required
@require_POST
def request_reject(request, pk: int):
    obj = get_object_or_404(VendorRequest, pk=pk)
    if not request.user.is_staff:
        raise PermissionDenied

    reason = (request.POST.get("reason") or "").strip()

    flow = VendorRequestFlow(obj)
    try:
        flow.reject(request.user, reason=reason)
    except TransitionNotAllowed:
        return HttpResponseBadRequest("Transition not allowed from current state")

    if request.headers.get("HX-Request") == "true":
        html = render_to_string(
            "third_party/partials/request_row.html", {"obj": obj}, request
        )
        return HttpResponse(html)
    return redirect("third_party:request_detail", pk=obj.pk)
