from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Veiculo(models.Model):
    placa = models.CharField(max_length=10, unique=True)
    descricao = models.CharField(max_length=100, blank=True, default="")
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.placa} - {self.descricao}".strip(" - ")

class Viagem(models.Model):
    STATUS_CHOICES = (
        ("PLANEJADA", "Planejada"),
        ("EM_ANDAMENTO", "Em andamento"),
        ("FECHADA", "Fechada"),
        ("CANCELADA", "Cancelada"),
    )

    origem = models.ForeignKey("estoque.Loja", on_delete=models.PROTECT, related_name="viagens_origem")
    destino = models.ForeignKey("estoque.Loja", on_delete=models.PROTECT, related_name="viagens_destino")
    responsavel = models.ForeignKey(User, on_delete=models.PROTECT, related_name="viagens_responsavel")
    veiculo = models.ForeignKey(Veiculo, on_delete=models.PROTECT, related_name="viagens")
    data_partida = models.DateTimeField()
    data_retorno = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PLANEJADA")
    motivo = models.CharField(max_length=200, blank=True, default="")
    referencia_os = models.ForeignKey("ordens.OrdemServico", on_delete=models.SET_NULL, null=True, blank=True, related_name="viagens")
    observacoes = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Viagem"
        verbose_name_plural = "Viagens"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["data_partida"]),
            models.Index(fields=["origem", "destino"]),
        ]

    def __str__(self):
        return f"{self.id} - {self.origem} → {self.destino} ({self.status})"
