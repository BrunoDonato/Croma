from django.contrib import admin
from .models import PrestadorServico, OrdemExterna


@admin.register(PrestadorServico)
class PrestadorServicoAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo_servico", "cidade", "telefone", "ativo")
    list_filter = ("ativo", "cidade", "tipo_servico")
    search_fields = ("nome", "cidade", "tipo_servico")


@admin.register(OrdemExterna)
class OrdemExternaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "equipamento",
        "loja",
        "prestador",
        "status",
        "prioridade",
        "data_envio",
        "data_previsao_retorno",
    )
    list_filter = ("status", "prioridade", "loja", "prestador")
    search_fields = ("equipamento", "numero_serie", "numero_os_prestador")
