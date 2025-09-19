from django.db import models

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

    quantidade = models.PositiveIntegerField(default=0)   # <<--- NOVO CAMPO
    estoque_minimo = models.PositiveIntegerField(default=0)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome

