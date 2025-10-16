from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from django.apps import apps
from django.contrib.auth import get_user_model
from .models import Perfil

User = get_user_model()

@receiver(post_migrate)
def ensure_default_groups(sender, **kwargs):
    if sender.label != apps.get_app_config('contas').label:
        return
    admin_group, _ = Group.objects.get_or_create(name="admin")
    user_group, _ = Group.objects.get_or_create(name="user")
    perms = Permission.objects.all()
    admin_group.permissions.set(perms)
    admin_group.save()
    user_group.save()

@receiver(post_save, sender=User)
def criar_perfil(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(user=instance)
