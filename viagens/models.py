from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class Veiculo(models.Model):
    placa = models.CharField(max_length=10, unique=True)
    descricao = models.CharField(max_length=100, blank=True, default="")
    ativo = models.BooleanField(default=True)

    def __str__(self):
        # strip(" - ") remove caracteres, não o sufixo; fazemos condicional.
        return f"{self.placa} - {self.descricao}" if self.descricao else self.placa


class Viagem(models.Model):
    STATUS = (
        ("PLANEJADA", "Planejada"),
        ("EM_ANDAMENTO", "Em andamento"),
        ("FECHADA", "Fechada"),
        ("CANCELADA", "Cancelada"),
    )

    referencia_os = models.ForeignKey(
        "ordens.OrdemServico",
        on_delete=models.PROTECT,
        related_name="viagens",
        null=True,
        blank=True,
    )
    origem = models.ForeignKey(
        "estoque.Loja",
        on_delete=models.PROTECT,
        related_name="viagens_origem",
    )
    destino = models.ForeignKey(
        "estoque.Loja",
        on_delete=models.PROTECT,
        related_name="viagens_destino",
    )
    responsavel = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="viagens_responsavel",
    )
    veiculo = models.ForeignKey(
        Veiculo,
        on_delete=models.PROTECT,
        related_name="viagens",
        null=True,
        blank=True,
    )
    data_partida = models.DateTimeField()
    data_retorno = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="PLANEJADA")
    motivo = models.CharField(max_length=200, blank=True, default="")
    observacoes = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Viagem"
        verbose_name_plural = "Viagens"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["data_partida"]),
            models.Index(fields=["origem", "destino"]),
        ]
        ordering = ("-data_partida",)

    def clean(self):
        errors = {}

        # Origem e destino não podem ser iguais (só valida se ambos existem)
        if self.origem_id and self.destino_id and self.origem_id == self.destino_id:
            errors["destino"] = "Origem e destino devem ser lojas diferentes."

        # Retorno não pode ser anterior à partida
        if self.data_partida and self.data_retorno and self.data_retorno < self.data_partida:
            errors["data_retorno"] = "Data de retorno não pode ser anterior à partida."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        origem = str(self.origem) if self.origem_id else "—"
        destino = str(self.destino) if self.destino_id else "—"
        return f"{self.id or '—'} - {origem} → {destino} ({self.status})"
