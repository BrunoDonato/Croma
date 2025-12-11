from django.db import models
from django.conf import settings

from estoque.models import Loja
from ordens.models import OrdemServico


class PrestadorServico(models.Model):
    nome = models.CharField("Nome fantasia", max_length=150)
    telefone = models.CharField("Telefone", max_length=20, blank=True, null=True)
    email = models.EmailField("E-mail", blank=True, null=True)
    cidade = models.CharField("Cidade", max_length=100, blank=True, null=True)
    tipo_servico = models.CharField("Tipo de serviço", max_length=100)
    ativo = models.BooleanField("Ativo", default=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class OrdemExterna(models.Model):
    STATUS_CHOICES = [
        ("ABERTA", "Aberta (aguardando envio)"),
        ("ENVIADA", "Enviada ao prestador"),
        ("EM_ANALISE", "Em análise"),
        ("AG_ORCAMENTO", "Aguardando orçamento"),
        ("APROVADA", "Aprovada (em execução)"),
        ("AG_PECA", "Aguardando peça"),
        ("CONCLUIDA", "Concluída"),
        ("CANCELADA", "Cancelada"),
    ]

    PRIORIDADE_CHOICES = [
        ("B", "Baixa"),
        ("M", "Média"),
        ("A", "Alta"),
        ("C", "Crítica"),
    ]

    loja = models.ForeignKey(
        Loja,
        on_delete=models.PROTECT,
        verbose_name="Loja / Local de estoque",
    )
    prestador = models.ForeignKey(
        PrestadorServico,
        on_delete=models.PROTECT,
        verbose_name="Prestador",
    )
    os_interna = models.ForeignKey(
        OrdemServico,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="OS interna",
    )

    equipamento = models.CharField("Equipamento", max_length=150)
    numero_serie = models.CharField("Número de série", max_length=80, blank=True, null=True)
    descricao_defeito = models.TextField("Descrição do defeito")

    status = models.CharField("Status", max_length=20, choices=STATUS_CHOICES, default="ABERTA")
    prioridade = models.CharField("Prioridade", max_length=1, choices=PRIORIDADE_CHOICES, default="M")

    data_envio = models.DateField("Data de envio", blank=True, null=True)
    data_previsao_retorno = models.DateField("Previsão de retorno", blank=True, null=True)
    data_retorno = models.DateField("Data de retorno", blank=True, null=True)

    numero_os_prestador = models.CharField("Nº OS prestador", max_length=80, blank=True, null=True)

    valor_orcado = models.DecimalField("Valor orçado", max_digits=10, decimal_places=2, null=True, blank=True)
    valor_aprovado = models.DecimalField("Valor aprovado", max_digits=10, decimal_places=2, null=True, blank=True)

    observacoes = models.TextField("Observações", blank=True, null=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Criado por",
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-criado_em"]

    def __str__(self):
        return f"OS Externa {self.id} - {self.equipamento}"
