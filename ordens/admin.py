from django.contrib import admin
from .models import OrdemServico

@admin.register(OrdemServico)
class OrdemServicoAdmin(admin.ModelAdmin):
    list_display = ("id", "loja", "solicitante", "prioridade", "status", "data_abertura", "data_fechamento", "tecnico_responsavel")
    list_filter = ("status", "prioridade", "loja")
    search_fields = ("id", "descricao_problema", "observacoes")
    date_hierarchy = "data_abertura"
