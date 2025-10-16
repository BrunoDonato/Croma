from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class OrdemServico(models.Model):
    PRIORIDADE_CHOICES = (
        ("BAIXA", "Baixa"),
        ("MEDIA", "Média"),
        ("ALTA", "Alta"),
        ("CRITICA", "Crítica"),
    )
    STATUS_CHOICES = (
        ("ABERTA", "Aberta"),
        ("EM_ANALISE", "Em análise"),
        ("EM_EXECUCAO", "Em execução"),
        ("FINALIZADA", "Finalizada"),
        ("CANCELADA", "Cancelada"),
    )

    loja = models.ForeignKey("estoque.Loja", on_delete=models.PROTECT, related_name="ordens")
    solicitante = models.ForeignKey(User, on_delete=models.PROTECT, related_name="ordens_solicitadas")
    descricao_problema = models.TextField()
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE_CHOICES, default="MEDIA")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="ABERTA")
    data_abertura = models.DateTimeField(auto_now_add=True)
    data_fechamento = models.DateTimeField(null=True, blank=True)
    tecnico_responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="ordens_designadas")
    observacoes = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Ordem de Serviço"
        verbose_name_plural = "Ordens de Serviço"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["prioridade"]),
            models.Index(fields=["data_abertura"]),
        ]

    def __str__(self):
        return f"OS-{self.id} | {self.loja} | {self.status}"
