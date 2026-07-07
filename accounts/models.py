"""
accounts — users ↔ authorities (P05.1). Membership is the seam Arc C governance hangs off:
who may ratify (P05.4), and later interval-scoped authority (Authority.scope_unit — see P05 §확장 지점).
"""
from django.conf import settings
from django.db import models


class Membership(models.Model):
    """A user's role within an Authority (ICS / subcommission / personal fork)."""
    class Role(models.TextChoices):
        OWNER = "owner", "owner"        # personal fork owner
        MEMBER = "member", "member"
        CHAIR = "chair", "chair"        # may ratify on behalf of the authority

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    authority = models.ForeignKey("chrono.Authority", on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=8, choices=Role.choices, default=Role.MEMBER)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "authority"], name="uniq_membership_user_authority"),
        ]
        ordering = ["authority__name", "user__username"]

    def __str__(self):
        return f"{self.user} @ {self.authority} ({self.role})"
