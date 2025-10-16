from django.db import models
from django.db.models import Q

class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome

class Produto(models.Model):
    nome = models.CharField(max_length=150, unique=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="produtos")
    unidade = models.CharField(max_length=10, help_text="Ex: un, cx, kg, m")

    fabricante = models.CharField(max_length=100, blank=True, null=True)
    modelo = models.CharField(max_length=100, blank=True, null=True)
    especificacoes = models.TextField(blank=True, null=True, help_text="Detalhes técnicos, voltagem, dimensões, etc.")

    estoque_minimo = models.PositiveIntegerField(
        "Saldo mínimo (Central)",
        default=0
        )
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome

class Loja(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    endereco = models.CharField(max_length=255, blank=True)
    ativa = models.BooleanField(default=True)
    is_central = models.BooleanField(default=False)  # Onde vou definir qual é meu estoque central

    class Meta:
        verbose_name = "Loja / Local de Estoque"
        verbose_name_plural = "Lojas / Locais de Estoque"
        ordering = ["nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["is_central"],
                condition=Q(is_central=True),
                name="uniq_loja_central_true",
            ),
        ]

    def __str__(self):
        return self.nome

class SaldoEstoque(models.Model):
    produto = models.ForeignKey("Produto", on_delete=models.CASCADE, related_name="saldos")
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name="saldos")
    quantidade = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Saldo de Estoque"
        verbose_name_plural = "Saldos de Estoque"
        constraints = [
            models.UniqueConstraint(fields=["produto", "loja"], name="uniq_produto_loja")
        ]
        indexes = [
            models.Index(fields=["produto", "loja"]),
            models.Index(fields=["loja", "quantidade"]),  # Indice para filtrar > 0 por loja
        ]
        ordering = ["produto__nome", "loja__nome"]

    def __str__(self):
        return f"{self.produto} @ {self.loja}: {self.quantidade}"