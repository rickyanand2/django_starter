# Django settings for a starter project.

import os
import sys
from pathlib import Path

# NEW: load .env early (if installed)
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file if python-dotenv is installed
if load_dotenv:
    load_dotenv(BASE_DIR / ".env")


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/


# SECURITY WARNING: don't run with debug turned on in production!
# --- Core toggles from env (.env now works) ---
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-change-me")


# UPDATED ###############
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,*").split(",")

# ADDED ###############
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.getenv("DJANGO_CSRF_TRUSTED", "").split(",") if o.strip()
]

# ADDED ###############
SITE_ID = int(os.getenv("SITE_ID", "1"))

# --- Domains & env for URL building (KISS) ---
BASE_DOMAIN = os.getenv("BASE_DOMAIN", "localhost")   # apex/public, e.g. "yourapp.com" or "localhost"
DEV_PORT = os.getenv("DEV_PORT", "8000")              # runserver port in dev
DEFAULT_SCHEME = "https" if not DEBUG else "http"


# ---------- apps ----------

SHARED_APPS = [
    "django_tenants",  # must be first
    "tenancy",  # app with the tenant model
    
    # Django Apps
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",  # admin on public schema
    "django.contrib.sites",
    
    # Third-party apps
    "django_htmx",

    # Allauth (for auth)
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    
    # Workflow apps
    "django_fsm",  # django-fsm-2
    "django_fsm_log",  # transition logging
       
    "core",  # Main website app
   
]

TENANT_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",  # admin on public schema
    "django.contrib.sites",

    # Third-party apps
    "django_htmx",

    # Allauth (for auth)
    "allauth",
    "allauth.account",
    "allauth.socialaccount",

    # Workflow apps
    "django_fsm",  # django-fsm-2
    "django_fsm_log",  # transition logging

    # your per-tenant apps (add as you go)
    "third_party",

]

INSTALLED_APPS = (list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]) + (
    ["debug_toolbar"] if DEBUG else []
)


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Custom context processors
                "tenancy.context_processors.branding",
                "tenancy.context_processors.is_public",
            ],
        },
    },
]


WSGI_APPLICATION = "config.wsgi.application"


# ---------- Database ----------
DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": os.getenv("POSTGRES_DB", "multitenant_db"),
        "USER": os.getenv("POSTGRES_USER", "postgres"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "4200"),
        "HOST": os.getenv("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

""" 
# Working database with sqlite fallback

# Use dj_database_url to parse the DATABASE_URL environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if DATABASE_URL:
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)}

else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
"""

# Tenant settings
TENANT_MODEL = "tenancy.Client"  # app.Model that contains the tenant info
TENANT_DOMAIN_MODEL = "tenancy.Domain"  # app.Model for domain names
SHOW_PUBLIC_IF_NO_TENANT_FOUND = True  # display public schema if no tenant found
# URL routing

PUBLIC_SCHEMA_URLCONF = "config.urls_public"  # For public schema
TENANT_BASE_URLCONF = "config.urls_tenants"    # tenant hosts

# Default URLConf (django-tenants will swap it per request)
ROOT_URLCONF = "config.urls_public"


# Old
#ROOT_URLCONF = "config.urls"

DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)



# ---------- End Database ----------

# ---------- Middleware ----------
MIDDLEWARE = [
    "django_tenants.middleware.main.TenantMainMiddleware",  # Must be first for django-tenants
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # REQUIRED by allauth
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Third-party middleware
    "django_htmx.middleware.HtmxMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
]

if DEBUG:
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
# ---------- End Middleware ----------

"""
# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

"""


AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

ACCOUNT_LOGIN_METHODS = {"email"}

# Fields collected on the signup form.
# A trailing * means "required". Here: email + passwords required;
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]


# ACCOUNT_EMAIL_VERIFICATION = os.getenv("ACCOUNT_EMAIL_VERIFICATION", "optional")
ACCOUNT_EMAIL_VERIFICATION = "none"

# Login redirect URL
LOGIN_URL = "account_login"
LOGIN_REDIRECT_URL = "/post-login/"  # after login → app shell
# Logout redirect URL
LOGOUT_REDIRECT_URL = "/post-logout/"


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Australia/Melbourne"
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images) -------------------
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"
# Whitenoise settings
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
}
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
MEDIAFILES_DIRS = [BASE_DIR / "media"]
# ---------- End Static files ----------


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "1025"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "0") == "1"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "webmaster@localhost")

# Show the "remember me" checkbox on the login form
# ACCOUNT_SESSION_REMEMBER = False
""" 
# ---------- Email (Mailpit in dev) ----------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "1025"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "0") == "1"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "webmaster@localhost")
"""

############################################################################
# ---------- Security (auto-on when DEBUG=0) ----------
############################################################################
INTERNAL_IPS = ["127.0.0.1", "localhost"]

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))  # set to 31536000 in real prod
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "0") == "1"
    SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "0") == "1"

############################################################################


############################################################################
# UPDATE FOR TESTS
############################################################################

# Detect if we're running tests
TESTING = any(arg in sys.argv for arg in ["test", "pytest"])

if TESTING:
    # 1) Use non-manifest static storage so tests don't need collectstatic
    # (Django 4.2+/5.x STORAGES API)
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }

    # 2) Strip middleware that depends on INSTALLED_APPS entries
    MIDDLEWARE = [ mw for mw in MIDDLEWARE if mw not in (
            "whitenoise.middleware.WhiteNoiseMiddleware",
            "debug_toolbar.middleware.DebugToolbarMiddleware",
        )
    ]

    # 3) Remove debug toolbar app entirely in tests
    INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "debug_toolbar"]

############################################################################
############################################################################
# UPDATE FOR LOGGING
############################################################################

# Optional: cache pending logs before DB persistence (advanced)
# DJANGO_FSM_LOG_STORAGE_METHOD = "django_fsm_log.backends.CachedBackend"
# DJANGO_FSM_LOG_CACHE_BACKEND = "default"

# Optional: disable logging for specific models
# DJANGO_FSM_LOG_IGNORED_MODELS = ("third_party.models.SomeModel",)

############################################################################