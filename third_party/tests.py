# third_party/tests.py
import pytest
from django.contrib.auth import get_user_model
from django.urls import resolve, reverse
from django_fsm import TransitionNotAllowed
from django_fsm_log.models import StateLog

from .forms import ThirdPartyRequestForm
from .models import RequestState, ThirdPartyRequest

User = get_user_model()


@pytest.fixture(autouse=True)
def _patch_staticfiles_storage(monkeypatch):
    """
    Some modules cache `staticfiles_storage` at import time (e.g., template tag,
    debug toolbar panel). Swap all known references to a simple storage so
    templates don't explode on missing manifest entries during tests.
    """
    from django.contrib.staticfiles.storage import StaticFilesStorage

    storage = StaticFilesStorage()

    # Core storage module
    import django.contrib.staticfiles.storage as s1

    monkeypatch.setattr(s1, "staticfiles_storage", storage, raising=False)

    # The `{% static %}` template tag module caches it too
    import django.templatetags.static as s2

    monkeypatch.setattr(s2, "staticfiles_storage", storage, raising=False)

    # Debug toolbar staticfiles panel (present in dev/test)
    try:
        import debug_toolbar.panels.staticfiles as s3  # type: ignore

        monkeypatch.setattr(s3, "staticfiles_storage", storage, raising=False)
    except Exception:
        pass


# ---------- test settings tweaks (avoid staticfiles/toolbar issues) ----------
@pytest.fixture(autouse=True)
def _staticfiles_simple_storage(settings):
    # Use plain storage so missing manifest entries don't blow up rendering
    settings.STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
    # Optional: disable Debug Toolbar’s staticfiles panel effects (if present)
    settings.DEBUG = False


# --------------------------- helpers / factories ----------------------------


def _make_user(email: str, *, password: str = "x", is_staff: bool = False):
    """
    Works with username- or email-based user models.
    """
    kwargs = {"is_staff": is_staff}
    if getattr(User, "USERNAME_FIELD", "username") == "email":
        return User.objects.create_user(email=email, password=password, **kwargs)
    username = email.split("@", 1)[0] or "user"
    return User.objects.create_user(username=username, email=email, password=password, **kwargs)


@pytest.fixture()
def user(db):
    return _make_user("user@example.com")


@pytest.fixture()
def staff(db):
    return _make_user("staff@example.com", is_staff=True)


@pytest.fixture()
def another_user(db):
    return _make_user("other@example.com")


@pytest.fixture()
def req(user):
    return ThirdPartyRequest.objects.create(
        name="Acme",
        description="Init",
        assignee=user,
        created_by=user,
    )


# =============================== Models =====================================


@pytest.mark.django_db
def test_model_happy_path_submit_then_approve_logs_actor(req, user):
    # Draft -> Review
    assert req.state == RequestState.ONBOARDING
    req.submit_for_review(by=user)
    req.save()
    assert req.state == RequestState.REVIEW
    assert StateLog.objects.for_(req).filter(state=RequestState.REVIEW, by=user).exists()

    # Review -> Approved
    req.approve(by=user)
    req.save()
    assert req.state == RequestState.APPROVED
    assert StateLog.objects.for_(req).filter(state=RequestState.APPROVED, by=user).exists()


@pytest.mark.django_db
def test_model_reject_requires_reason_and_logs(req, user):
    with pytest.raises(ValueError):
        req.reject(reason="", by=user)

    req.reject(reason="Missing docs", by=user)
    req.save()
    assert req.state == RequestState.REJECTED
    assert req.reject_reason == "Missing docs"
    assert StateLog.objects.for_(req).filter(state=RequestState.REJECTED, by=user).exists()


@pytest.mark.django_db
def test_model_invalid_transition_blocked(req, user):
    with pytest.raises(TransitionNotAllowed):
        req.approve(by=user)


# =============================== Forms ======================================


@pytest.mark.django_db
def test_form_requires_assignee(user):
    form = ThirdPartyRequestForm(data={"name": "No Assignee", "description": "x"})
    assert not form.is_valid()
    assert "assignee" in form.errors


@pytest.mark.django_db
def test_form_valid_with_assignee(user):
    form = ThirdPartyRequestForm(
        data={"name": "With Assignee", "description": "x", "assignee": user.pk}
    )
    assert form.is_valid()


# ================================ URLs ======================================


def test_urlnames_resolve():
    assert resolve(reverse("third_party:request_list")).url_name == "request_list"
    assert resolve(reverse("third_party:request_list_assigned")).url_name == "request_list_assigned"
    assert resolve(reverse("third_party:request_create")).url_name == "request_create"
    reverse("third_party:request_list")  # smoke


# ================================ Views =====================================


def _reload(obj):
    # Avoid refresh_from_db(), which conflicts with protected FSMField
    return obj.__class__.objects.get(pk=obj.pk)


@pytest.mark.django_db
def test_non_assignee_cannot_submit(client, req, another_user):
    client.force_login(another_user)
    url = reverse("third_party:request_submit", args=[req.pk])
    resp = client.post(url, follow=False)  # avoid rendering templates
    assert resp.status_code == 403
    req = _reload(req)
    assert req.state == RequestState.ONBOARDING


@pytest.mark.django_db
def test_assignee_can_submit_then_approve(client, req, user):
    client.force_login(user)

    submit = reverse("third_party:request_submit", args=[req.pk])
    resp = client.post(submit, follow=False)  # no render
    assert resp.status_code in (302, 200)
    req = _reload(req)
    assert req.state == RequestState.REVIEW

    approve = reverse("third_party:request_approve", args=[req.pk])
    resp = client.post(approve, follow=False)  # no render
    assert resp.status_code in (302, 200)
    req = _reload(req)
    assert req.state == RequestState.APPROVED


@pytest.mark.django_db
def test_staff_can_transition_even_if_not_assignee(client, req, staff):
    client.force_login(staff)
    submit = reverse("third_party:request_submit", args=[req.pk])
    resp = client.post(submit, follow=False)  # no render
    assert resp.status_code in (302, 200)
    req = _reload(req)
    assert req.state == RequestState.REVIEW


@pytest.mark.django_db
def test_reject_requires_post_and_reason(client, req, user):
    client.force_login(user)
    reject = reverse("third_party:request_reject", args=[req.pk])

    # GET should 404
    resp = client.get(reject, follow=False)
    assert resp.status_code == 404

    # POST without reason -> remains Draft
    resp = client.post(reject, data={"reason": ""}, follow=False)
    assert resp.status_code in (302, 200)
    req = _reload(req)
    assert req.state == RequestState.ONBOARDING

    # POST with reason -> Rejected
    resp = client.post(reject, data={"reason": "Not enough docs"}, follow=False)
    assert resp.status_code in (302, 200)
    req = _reload(req)
    assert req.state == RequestState.REJECTED
    assert req.reject_reason == "Not enough docs"


@pytest.mark.django_db
def test_list_views_filter_by_state(client, user, staff):
    r1 = ThirdPartyRequest.objects.create(name="R1", assignee=user, created_by=user)
    r2 = ThirdPartyRequest.objects.create(name="R2", assignee=staff, created_by=staff)

    r2.submit_for_review(by=staff)
    r2.save()

    client.force_login(user)

    # we still render this page, but with simple staticfiles storage it won't error
    list_url = reverse("third_party:request_list") + f"?state={RequestState.REVIEW}"
    resp = client.get(list_url)
    assert resp.status_code == 200
    assert "R2" in resp.content.decode()

    mine_url = reverse("third_party:request_list_assigned") + f"?state={RequestState.REVIEW}"
    resp = client.get(mine_url)
    assert resp.status_code == 200
    assert "R2" not in resp.content.decode()


# ============================== Misc ========================================


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
