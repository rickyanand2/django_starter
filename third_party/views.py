# third_party/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django_fsm import TransitionNotAllowed
from django_fsm_log.models import StateLog

from tenancy.guards import require_membership
from .forms import ThirdPartyRequestForm
from .models import RequestState, ThirdPartyRequest

@require_membership("member")
def dashboard(request):
    return render(request, "third_party/dashboard.html")

def _can_transition(user, obj: ThirdPartyRequest) -> bool:
    return user.is_staff or (obj.assignee_id == user.id)

@require_membership("member")
@login_required
def request_list(request):
    qs = ThirdPartyRequest.objects.select_related("assignee", "created_by").order_by("-created_at")
    state = request.GET.get("state")
    if state:
        qs = qs.filter(state=state)
    return render(request, "third_party/request_list.html", {"requests": qs, "active_state": state})

@require_membership("member")
@login_required
def request_list_assigned(request):
    qs = (ThirdPartyRequest.objects.select_related("assignee", "created_by")
          .filter(assignee=request.user).order_by("-created_at"))
    state = request.GET.get("state")
    if state:
        qs = qs.filter(state=state)
    return render(request, "third_party/request_list.html", {"requests": qs, "active_state": state, "only_mine": True})

@require_membership("member")
@login_required
def request_detail(request, pk):
    obj = get_object_or_404(ThirdPartyRequest, pk=pk)
    logs = StateLog.objects.for_(obj).select_related("by").order_by("-timestamp")
    return render(request, "third_party/request_detail.html", {
        "object": obj,
        "can_transition": _can_transition(request.user, obj),
        "logs": logs,
    })

@require_membership("member")
@login_required
def request_list_draft(request):
    return request_list_with_state(request, RequestState.ONBOARDING)

@require_membership("member")
@login_required
def request_list_review(request):
    return request_list_with_state(request, RequestState.REVIEW)

@require_membership("member")
@login_required
def request_list_approved(request):
    return request_list_with_state(request, RequestState.APPROVED)

@require_membership("member")
@login_required
def request_list_rejected(request):
    return request_list_with_state(request, RequestState.REJECTED)

def request_list_with_state(request, state_value):
    qs = (ThirdPartyRequest.objects.select_related("assignee", "created_by")
          .filter(state=state_value).order_by("-created_at"))
    return render(request, "third_party/request_list.html", {"requests": qs, "active_state": state_value})

@require_membership("member")
@login_required
def request_create(request):
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

@require_membership("member")
@login_required
def request_submit(request, pk):
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

@require_membership("member")
@login_required
def request_approve(request, pk):
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

@require_membership("member")
@login_required
def request_reject(request, pk):
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
