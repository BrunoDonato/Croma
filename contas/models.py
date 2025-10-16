from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil")
    loja = models.ForeignKey("estoque.Loja", on_delete=models.PROTECT, related_name="usuarios", null=True, blank=True)

    def __str__(self):
        return f"{self.user}"
