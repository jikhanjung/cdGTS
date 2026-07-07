"""On user creation, mint a personal fork Authority the user owns (their sandbox home)."""
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from chrono.models import Authority
from .models import Membership

User = get_user_model()


@receiver(post_save, sender=User, dispatch_uid="accounts.create_personal_authority")
def create_personal_authority(sender, instance, created, **kwargs):
    if not created:
        return
    authority, _ = Authority.objects.get_or_create(
        slug=f"user-{instance.pk}",
        defaults={"name": f"{instance.get_username()}'s fork", "kind": Authority.Kind.FORK},
    )
    Membership.objects.get_or_create(
        user=instance, authority=authority, defaults={"role": Membership.Role.OWNER},
    )
