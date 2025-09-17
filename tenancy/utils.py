# tenancy/utils.py
import re
from urllib.parse import urlunparse
from django.conf import settings

def normalize_schema_name(subdomain: str) -> str:
    s = (subdomain or "").strip().lower()
    s = re.sub(r"[^a-z0-9_]", "_", s)
    if s == "public":
        s = "public_org"
    return s[:63] or "org"

def make_tenant_domain(subdomain: str) -> str:
    """
    Bare host, no scheme/port. e.g. 'acme.localhost' or 'acme.yourapp.com'.
    """
    sub = (subdomain or "").strip().lower()
    base = settings.BASE_DOMAIN.strip()
    return f"{sub}.{base}" if sub else base

def build_public_url(path: str = "/") -> str:
    scheme = settings.DEFAULT_SCHEME
    netloc = settings.BASE_DOMAIN
    if settings.DEBUG and settings.DEV_PORT:
        netloc = f"{netloc}:{settings.DEV_PORT}"
    return urlunparse((scheme, netloc, path or "/", "", "", ""))

def build_tenant_url(domain: str, path: str = "/") -> str:
    scheme = settings.DEFAULT_SCHEME
    netloc = domain
    if settings.DEBUG and settings.DEV_PORT:
        netloc = f"{netloc}:{settings.DEV_PORT}"
    return urlunparse((scheme, netloc, path or "/", "", "", ""))
