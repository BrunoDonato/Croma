from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

class Command(BaseCommand):
    help = "Cria grupos padrão e usuários de teste"

    def handle(self, *args, **kwargs):
        admin_group, _ = Group.objects.get_or_create(name="admin")
        user_group, _ = Group.objects.get_or_create(name="user")

        if not User.objects.filter(username="teste").exists():
            u = User.objects.create_user(username="teste", email="teste@example.com", password="123456")
            u.groups.add(user_group)

        if not User.objects.filter(username="admin").exists():
            a = User.objects.create_user(username="admin", email="admin@example.com", password="123456")
            a.is_staff = True
            a.save()
            a.groups.add(admin_group)

        self.stdout.write(self.style.SUCCESS("Grupos e usuários de teste criados"))
