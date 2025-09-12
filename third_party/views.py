# third_party/views.py
"""
Purpose
-------
App-level orchestrators (HTTP endpoints) that:
- Authorize the actor (assignee or staff).
- Call pure model transitions (which log themselves).
- Persist with a minimal save() (state & updated_at).

Design
------
- Keep views thin; push domain rules to the model.
- No business logic in templates.

Testability
-----------
- Each view can be unit-tested with request factories:
  - 403 when user isn't assignee/staff
  - Success path changes state & sets messages
  - Rejection without reason returns error message
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django_fsm import TransitionNotAllowed

from django_fsm_log.models import StateLog

from .models import ThirdPartyRequest, RequestState
from .forms import ThirdPartyRequestForm


def _can_transition(user, obj: ThirdPartyRequest) -> bool:
    """Authorization guard: only assignee (or staff) can transition."""
    return user.is_staff or (obj.assignee_id == user.id)


# ---------- List & Detail ----------


@login_required
def request_list(request):
    """
    All requests. Optional ?state= filter also supported.
    Template expects 'requests' not 'object_list'.
    """
    qs = ThirdPartyRequest.objects.select_related("assignee", "created_by").order_by(
        "-created_at"
    )
    state = request.GET.get("state")
    if state:
        qs = qs.filter(state=state)
    ctx = {"requests": qs, "active_state": state}
    return render(request, "third_party/request_list.html", ctx)


@login_required
def request_list_assigned(request):
    """
    Requests assigned to me. Optional ?state= filter.
    """
    qs = (
        ThirdPartyRequest.objects.select_related("assignee", "created_by")
        .filter(assignee=request.user)
        .order_by("-created_at")
    )
    state = request.GET.get("state")
    if state:
        qs = qs.filter(state=state)
    ctx = {"requests": qs, "active_state": state, "only_mine": True}
    return render(request, "third_party/request_list.html", ctx)


@login_required
def request_detail(request, pk):
    """Read-only summary page with context actions decided by current state."""
    obj = get_object_or_404(ThirdPartyRequest, pk=pk)
    can_trans = _can_transition(request.user, obj)

    # Most-recent-first audit trail for this object
    logs = StateLog.objects.for_(obj).select_related("by").order_by("-timestamp")

    ctx = {
        "object": obj,
        "can_transition": can_trans,
        "logs": logs,
    }
    return render(request, "third_party/request_detail.html", ctx)


# --- Convenience endpoints for sidebar quick filters (no query params) ---


@login_required
def request_list_draft(request):
    return request_list_with_state(request, RequestState.ONBOARDING)


@login_required
def request_list_review(request):
    return request_list_with_state(request, RequestState.REVIEW)


@login_required
def request_list_approved(request):
    return request_list_with_state(request, RequestState.APPROVED)


@login_required
def request_list_rejected(request):
    return request_list_with_state(request, RequestState.REJECTED)


def request_list_with_state(request, state_value):
    qs = (
        ThirdPartyRequest.objects.select_related("assignee", "created_by")
        .filter(state=state_value)
        .order_by("-created_at")
    )
    ctx = {"requests": qs, "active_state": state_value}
    return render(request, "third_party/request_list.html", ctx)


# ---------- Create ----------


@login_required
def request_create(request):
    """
    Create a new Draft request.
    - Sets created_by to current user.
    - Requires assignee via form validation.
    """
    if request.method == "POST":
        form = ThirdPartyRequestForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
            messages.success(request, "Request created.")
            return redirect("third_party:request_detail", pk=obj.pk)
    else:
        form = ThirdPartyRequestForm()
    return render(request, "third_party/request_form.html", {"form": form})


# ---------- Transitions ----------


@login_required
def request_submit(request, pk):
    """
    Draft -> Review
    - 403 if not assignee/staff.
    - Logs actor via fsm-log when calling with by=request.user.
    """
    obj = get_object_or_404(ThirdPartyRequest, pk=pk)
    if not _can_transition(request.user, obj):
        return HttpResponseForbidden("Only assignee or staff can transition.")
    try:
        obj.submit_for_review(by=request.user)
        obj.save(update_fields=["state", "updated_at"])
        messages.success(request, "Submitted for review.")
    except TransitionNotAllowed:
        messages.error(request, "Invalid transition from current state.")
    return redirect("third_party:request_detail", pk=obj.pk)


@login_required
def request_approve(request, pk):
    """
    Review -> Approved
    - 403 if not assignee/staff.
    """
    obj = get_object_or_404(ThirdPartyRequest, pk=pk)
    if not _can_transition(request.user, obj):
        return HttpResponseForbidden("Only assignee or staff can transition.")
    try:
        obj.approve(by=request.user)
        obj.save(update_fields=["state", "updated_at"])
        messages.success(request, "Approved.")
    except TransitionNotAllowed:
        messages.error(request, "Invalid transition from current state.")
    return redirect("third_party:request_detail", pk=obj.pk)


@login_required
def request_reject(request, pk):
    """
    Draft/Review -> Rejected
    - 403 if not assignee/staff.
    - Requires POST + reason; raises ValueError that we surface nicely.
    """
    obj = get_object_or_404(ThirdPartyRequest, pk=pk)
    if not _can_transition(request.user, obj):
        return HttpResponseForbidden("Only assignee or staff can transition.")
    if request.method != "POST":
        raise Http404()
    reason = (request.POST.get("reason") or "").strip()
    try:
        obj.reject(reason=reason, by=request.user)
        obj.save(update_fields=["reject_reason", "state", "updated_at"])
        messages.warning(request, "Rejected.")
    except ValueError as e:
        messages.error(request, str(e))
    except TransitionNotAllowed:
        messages.error(request, "Invalid transition from current state.")
    return redirect("third_party:request_detail", pk=obj.pk)
