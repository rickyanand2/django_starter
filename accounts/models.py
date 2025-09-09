from django.db import models
from django.conf import settings


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    job_title = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    country = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Profile of {self.user.email}"
