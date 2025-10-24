from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

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

    loja = models.ForeignKey(
        "estoque.Loja",
        on_delete=models.PROTECT,
        related_name="ordens"
    )
    solicitante = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="ordens_solicitadas"
    )
    descricao_problema = models.TextField()
    prioridade = models.CharField(
        max_length=10,
        choices=PRIORIDADE_CHOICES,
        default="MEDIA"
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default="ABERTA"
    )
    data_abertura = models.DateTimeField(auto_now_add=True)
    data_fechamento = models.DateTimeField(null=True, blank=True)
    tecnico_responsavel = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ordens_designadas"
    )
    observacoes = models.TextField(blank=True, default="")
    solucao = models.TextField(blank=True, default="")
    motivo_cancelamento = models.TextField(blank=True, default="")
    custo_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "Ordem de Serviço"
        verbose_name_plural = "Ordens de Serviço"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["prioridade"]),
            models.Index(fields=["data_abertura"]),
        ]
        ordering = ("-data_abertura",)

    def __str__(self):
        return f"OS-{self.id} | {self.loja} | {self.status}"

    # Propriedades
    @property
    def titulo_auto(self) -> str:
        base = getattr(self, "titulo", None) or (self.descricao_problema or "")
        txt = str(base).strip()
        if not txt:
            return ""
        return txt.splitlines()[0][:80]

    @property
    def descricao_texto(self) -> str:
        return self.descricao_problema or ""

    # Utilitários
    def fechar(self, tecnico: User | None = None, observacoes: str | None = None):
        self.status = "FINALIZADA"
        self.data_fechamento = timezone.now()
        if tecnico is not None:
            self.tecnico_responsavel = tecnico
        if observacoes:
            self.observacoes = (self.observacoes + "\n" if self.observacoes else "") + observacoes
        self.save(update_fields=["status", "data_fechamento", "tecnico_responsavel", "observacoes"])

    # Fluxo de status
    STATUS_FLOW = {
        "ABERTA": {"EM_ANALISE", "CANCELADA"},
        "EM_ANALISE": {"EM_EXECUCAO", "CANCELADA"},
        "EM_EXECUCAO": {"FINALIZADA", "CANCELADA"},
        "FINALIZADA": set(),
        "CANCELADA": set(),
    }

    class TransicaoInvalida(Exception):
        pass

    class CamposObrigatorios(Exception):
        pass

    def mudar_status(self, novo_status: str, autor: User, texto_andamento: str = "", visibilidade: str = "INTERNO"):
        atual = self.status
        if novo_status not in self.STATUS_FLOW.get(atual, set()):
            raise OrdemServico.TransicaoInvalida(f"Transição {atual} → {novo_status} não é permitida.")

        # Regras específicas
        if novo_status == "EM_EXECUCAO" and not self.tecnico_responsavel:
            raise OrdemServico.CamposObrigatorios("Defina o técnico responsável antes de iniciar a execução.")
        if novo_status == "FINALIZADA" and not self.solucao.strip():
            raise OrdemServico.CamposObrigatorios("Informe a solução antes de finalizar.")
        if novo_status == "CANCELADA" and not self.motivo_cancelamento.strip():
            raise OrdemServico.CamposObrigatorios("Informe o motivo do cancelamento.")

        # Atualiza o status e registra o histórico
        self.status = novo_status
        if novo_status == "FINALIZADA":
            self.data_fechamento = timezone.now()
        self.save()

        AndamentoOS.objects.create(
            os=self,
            autor=autor,
            texto=texto_andamento,
            visibilidade=visibilidade,
            status_de=atual,
            status_para=novo_status,
        )


# Histórico de Andamentos
class AndamentoOS(models.Model):
    VISIBILIDADE_CHOICES = (
        ("PUBLICO", "Público"),
        ("INTERNO", "Interno"),
    )

    os = models.ForeignKey(OrdemServico, on_delete=models.CASCADE, related_name="andamentos")
    autor = models.ForeignKey(User, on_delete=models.PROTECT)
    criado_em = models.DateTimeField(auto_now_add=True)
    texto = models.TextField(blank=True, default="")
    visibilidade = models.CharField(max_length=10, choices=VISIBILIDADE_CHOICES, default="PUBLICO")
    status_de = models.CharField(max_length=15, blank=True, default="")
    status_para = models.CharField(max_length=15, blank=True, default="")

    class Meta:
        ordering = ("-criado_em",)

    def __str__(self):
        return f"Andamento {self.os.id} por {self.autor}"


# Anexos
def os_upload_path(instance, filename):
    return f"os/{instance.os_id}/{filename}"

class AnexoOS(models.Model):
    os = models.ForeignKey(OrdemServico, on_delete=models.CASCADE, related_name="anexos")
    arquivo = models.FileField(upload_to=os_upload_path)
    enviado_por = models.ForeignKey(User, on_delete=models.PROTECT)
    enviado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-enviado_em",)

    def __str__(self):
        return f"Anexo OS-{self.os.id} ({self.arquivo.name})"
