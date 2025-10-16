from django.contrib import admin
from .models import Veiculo, Viagem

@admin.register(Veiculo)
class VeiculoAdmin(admin.ModelAdmin):
    list_display = ("placa", "descricao", "ativo")
    list_filter = ("ativo",)
    search_fields = ("placa", "descricao")

@admin.register(Viagem)
class ViagemAdmin(admin.ModelAdmin):
    list_display = ("id", "origem", "destino", "responsavel", "veiculo", "data_partida", "data_retorno", "status")
    list_filter = ("status", "origem", "destino", "veiculo")
    search_fields = ("id", "motivo", "referencia_os", "observacoes")
    date_hierarchy = "data_partida"
