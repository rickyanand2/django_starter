# accounts/tests.py
# -*- coding: utf-8 -*-
import pytest
from django.contrib.auth import get_user_model
from django.urls import NoReverseMatch, reverse

from accounts.models import Profile

# ---------- helpers ----------


def reverse_or_none(name: str):
    try:
        return reverse(name)
    except NoReverseMatch:
        return None


def url_exists(client, url: str) -> bool:
    if not url:
        return False
    resp = client.get(url)
    # If it redirects somewhere, it still "exists"
    return resp.status_code in (200, 301, 302, 303)


def create_test_user(email: str, password: str):
    """
    Create a user regardless of whether the project uses username or email auth.
    """
    User = get_user_model()
    kwargs = {"email": email}
    # If username is required, provide one
    if "username" in [f.name for f in User._meta.get_fields()]:
        kwargs.setdefault("username", email.split("@")[0])
    return User.objects.create_user(password=password, **kwargs)


# ---------- fixtures ----------


@pytest.fixture(autouse=True)
def _relax_staticfiles_for_tests(settings):
    """
    Avoid 'Missing staticfiles manifest entry' during template renders in tests.
    """
    settings.STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
    settings.WHITENOISE_AUTOREFRESH = True
    settings.DEBUG = True


# ---------- tests ----------


@pytest.mark.django_db
def test_allauth_routes_exist(client):
    # Accept 200 (render) or 302 (redirect) to be robust to env settings.
    for route_name, must_contain in [
        ("account_login", "Welcome back"),
        ("account_signup", "Create your account"),
        ("account_logout", "Sign out"),
    ]:
        url = reverse_or_none(route_name)
        assert url, f"Route {route_name} is not resolvable (is allauth included in urls.py?)"
        r = client.get(url, follow=False)
        assert r.status_code in (200, 302, 303)
        # Only assert HTML content if we actually rendered the page
        if r.status_code == 200:
            assert must_contain in r.content.decode()


@pytest.mark.django_db
def test_settings_requires_login(client):
    url = reverse_or_none("accounts:settings")
    if not url or not url_exists(client, url):
        pytest.skip("accounts:settings not wired in project urls yet.")
    r = client.get(url)
    # not logged in -> redirect to login
    assert r.status_code in (302, 303)
    login_url = reverse_or_none("account_login")
    assert login_url and login_url in r.headers.get("Location", "")


@pytest.mark.django_db
def test_profile_requires_login(client):
    url = reverse_or_none("accounts:profile")
    if not url or not url_exists(client, url):
        pytest.skip("accounts:profile not wired in project urls yet.")
    r = client.get(url)
    assert r.status_code in (302, 303)
    login_url = reverse_or_none("account_login")
    assert login_url and login_url in r.headers.get("Location", "")


@pytest.mark.django_db
def test_profile_get_renders_form_for_profile(client):
    """
    Happy-path once routed & view fixed to use a Profile instance.
    If route not present, skip. If view still bound to request.user, this may 500.
    """
    url = reverse_or_none("accounts:profile")
    if not url or not url_exists(client, url):
        pytest.skip("accounts:profile not wired in project urls yet.")

    user = create_test_user("u@example.com", "pass12345")
    Profile.objects.get_or_create(user=user)

    # Django's test client supports login by username; for email-only auth,
    # the backend may still accept username as the local-part.
    login_ok = client.login(
        username=getattr(user, "username", "u"), password="pass12345"
    ) or client.login(email="u@example.com", password="pass12345")
    assert login_ok, "Login failed in test setup."

    r = client.get(url)
    assert (
        r.status_code == 200
    ), "Expected profile form page to render (fix view to use Profile instance)."
    html = r.content.decode()
    assert 'name="job_title"' in html
    assert 'name="phone"' in html
    assert 'name="country"' in html
