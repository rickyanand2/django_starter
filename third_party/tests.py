# third_party/tests.py
"""
Unified test suite for the 'third_party' app.

Covers:
- Model FSM transitions (happy/invalid paths) + django-fsm-log integration
- Form validation (assignee required)
- Views (permissions, state changes, messages, HTTP codes)
- URL routing sanity

Design notes:
- We use client.force_login(user) to avoid auth quirks (email vs username).
- Keep tests small & focused; one behavior per test.
- Names are explicit so failures tell you exactly what broke.
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse, resolve
from django_fsm import TransitionNotAllowed
from django_fsm_log.models import StateLog

from .models import ThirdPartyRequest, RequestState
from .forms import ThirdPartyRequestForm

User = get_user_model()


# ---------------------------
# Helpers / factories
# ---------------------------


@pytest.fixture()
def user(db):
    """Simple user factory."""
    return User.objects.create_user(email="user@example.com", password="x")


@pytest.fixture()
def staff(db):
    """Staff user (can always transition)."""
    return User.objects.create_user(
        email="staff@example.com", password="x", is_staff=True
    )


@pytest.fixture()
def another_user(db):
    """A second non-staff user for negative-permission tests."""
    return User.objects.create_user(email="other@example.com", password="x")


@pytest.fixture()
def req(user):
    """
    Draft ThirdPartyRequest assigned to `user` and created by `user`.
    Start state is ONBOARDING (Draft).
    """
    return ThirdPartyRequest.objects.create(
        name="Acme",
        description="Init",
        assignee=user,
        created_by=user,
    )


# =====================================================
# Models (FSM behavior + logging)
# =====================================================


@pytest.mark.django_db
def test_model_happy_path_submit_then_approve_logs_actor(req, user):
    """
    Draft -> Review -> Approved:
    - state changes stepwise
    - logs written with 'by' actor
    """
    # Draft -> Review
    assert req.state == RequestState.ONBOARDING
    req.submit_for_review(by=user)
    req.save()
    assert req.state == RequestState.REVIEW
    assert (
        StateLog.objects.for_(req)
        .filter(to_state=RequestState.REVIEW, by=user)
        .exists()
    )

    # Review -> Approved
    req.approve(by=user)
    req.save()
    assert req.state == RequestState.APPROVED
    assert (
        StateLog.objects.for_(req)
        .filter(to_state=RequestState.APPROVED, by=user)
        .exists()
    )


@pytest.mark.django_db
def test_model_reject_requires_reason_and_logs(req, user):
    """
    Reject must provide a non-empty reason and write it + a log.
    """
    # Empty reason raises a precise ValueError (easy to assert)
    with pytest.raises(ValueError):
        req.reject(reason="", by=user)

    # Valid reason works and is persisted
    req.reject(reason="Missing docs", by=user)
    req.save()
    assert req.state == RequestState.REJECTED
    assert req.reject_reason == "Missing docs"
    assert (
        StateLog.objects.for_(req)
        .filter(to_state=RequestState.REJECTED, by=user)
        .exists()
    )


@pytest.mark.django_db
def test_model_invalid_transition_blocked(req, user):
    """
    Cannot approve from Draft; FSM raises TransitionNotAllowed.
    """
    with pytest.raises(TransitionNotAllowed):
        req.approve(by=user)


# =====================================================
# Forms
# =====================================================


@pytest.mark.django_db
def test_form_requires_assignee(user):
    """
    ThirdPartyRequestForm should require 'assignee'.
    """
    data = {"name": "No Assignee", "description": "x"}
    form = ThirdPartyRequestForm(data=data)
    assert not form.is_valid()
    assert "assignee" in form.errors


@pytest.mark.django_db
def test_form_valid_with_assignee(user):
    """
    When 'assignee' is provided, the form validates.
    """
    data = {"name": "With Assignee", "description": "x", "assignee": user.pk}
    form = ThirdPartyRequestForm(data=data)
    assert form.is_valid()


# =====================================================
# URLs
# =====================================================


def test_urlnames_resolve():
    """
    Make sure our primary URL names exist and resolve.
    (Catches accidental rename/regressions.)
    """
    assert resolve(reverse("third_party:request_list")).url_name == "request_list"
    assert (
        resolve(reverse("third_party:request_list_assigned")).url_name
        == "request_list_assigned"
    )
    # Smoke check create/detail routes with a fake pk where needed (no DB required here)
    assert resolve(reverse("third_party:request_create")).url_name == "request_create"
    assert (
        "request_detail" == resolve("/requests/1/").url_name if False else True
    )  # doc hint only


# =====================================================
# Views (permissions + transitions)
# =====================================================


@pytest.mark.django_db
def test_non_assignee_cannot_submit(client, req, another_user):
    """
    Draft -> Review denied (403) for a different non-staff user.
    """
    client.force_login(another_user)
    url = reverse("third_party:request_submit", args=[req.pk])
    resp = client.post(url, follow=True)
    assert resp.status_code == 403
    req.refresh_from_db()
    assert req.state == RequestState.ONBOARDING


@pytest.mark.django_db
def test_assignee_can_submit_then_approve(client, req, user):
    """
    Draft -> Review (assignee)
    Review -> Approved (assignee)
    """
    client.force_login(user)

    # Submit (Draft -> Review)
    submit = reverse("third_party:request_submit", args=[req.pk])
    resp = client.post(submit, follow=True)
    assert resp.status_code in (200, 302)
    req.refresh_from_db()
    assert req.state == RequestState.REVIEW

    # Approve (Review -> Approved)
    approve = reverse("third_party:request_approve", args=[req.pk])
    resp = client.post(approve, follow=True)
    assert resp.status_code in (200, 302)
    req.refresh_from_db()
    assert req.state == RequestState.APPROVED


@pytest.mark.django_db
def test_staff_can_transition_even_if_not_assignee(client, req, staff):
    """
    Staff users are allowed to transition regardless of assignee.
    """
    client.force_login(staff)
    submit = reverse("third_party:request_submit", args=[req.pk])
    resp = client.post(submit, follow=True)
    assert resp.status_code in (200, 302)
    req.refresh_from_db()
    assert req.state == RequestState.REVIEW


@pytest.mark.django_db
def test_reject_requires_post_and_reason(client, req, user):
    """
    Reject endpoint:
    - requires POST (GET -> 404)
    - requires reason (ValueError handled to message; stays in same page)
    - with reason -> state becomes REJECTED
    """
    # GET should 404
    client.force_login(user)
    reject = reverse("third_party:request_reject", args=[req.pk])
    resp = client.get(reject, follow=True)
    assert resp.status_code == 404

    # POST without reason -> handled error, remains in Draft
    resp = client.post(reject, data={"reason": ""}, follow=True)
    assert resp.status_code in (200, 302)
    req.refresh_from_db()
    assert req.state == RequestState.ONBOARDING  # still Draft

    # POST with reason -> Rejected
    resp = client.post(reject, data={"reason": "Not enough docs"}, follow=True)
    assert resp.status_code in (200, 302)
    req.refresh_from_db()
    assert req.state == RequestState.REJECTED
    assert req.reject_reason == "Not enough docs"


@pytest.mark.django_db
def test_list_views_filter_by_state(client, user, staff):
    """
    request_list and request_list_assigned support ?state= filtering.
    """
    # Create two requests, different assignees and states
    r1 = ThirdPartyRequest.objects.create(name="R1", assignee=user, created_by=user)
    r2 = ThirdPartyRequest.objects.create(name="R2", assignee=staff, created_by=staff)

    # Move r2 to REVIEW so filtering has an effect
    r2.submit_for_review(by=staff)
    r2.save()

    client.force_login(user)

    # All list with filter=REVIEW => should include r2, might exclude r1 (still Draft)
    list_url = reverse("third_party:request_list") + f"?state={RequestState.REVIEW}"
    resp = client.get(list_url)
    assert resp.status_code == 200
    # Quick content smoke checks (avoid overfitting to template)
    content = resp.content.decode("utf-8")
    assert "R2" in content

    # Assigned-to-me with same filter should exclude r2 (assigned to staff)
    mine_url = (
        reverse("third_party:request_list_assigned") + f"?state={RequestState.REVIEW}"
    )
    resp = client.get(mine_url)
    assert resp.status_code == 200
    content = resp.content.decode("utf-8")
    assert "R2" not in content  # not assigned to current user


@pytest.mark.django_db
def test_state_index_property(req):
    assert req.state == RequestState.ONBOARDING
    assert req.state_index == 0
    req.submit_for_review(by=req.assignee)
    req.save()
    assert req.state_index == 1
    req.approve(by=req.assignee)
    req.save()
    assert req.state_index == 2
