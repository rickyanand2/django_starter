# third_party/apps.py
from django.apps import AppConfig


class ThirdPartyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "third_party"

    def ready(self):
        from . import signals  # noqa: F401
