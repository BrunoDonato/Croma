from django.contrib import admin, messages
from django.db import transaction
from .models import Viagem, Veiculo

@admin.register(Veiculo)
class VeiculoAdmin(admin.ModelAdmin):
    list_display = ("placa","descricao","ativo")
    list_filter = ("ativo",)
    search_fields = ("placa","descricao")

@admin.register(Viagem)
class ViagemAdmin(admin.ModelAdmin):
    list_display = ("id","origem","destino","responsavel","data_partida","data_retorno","status")
    list_filter = ("status","origem","destino","responsavel")
    search_fields = ("motivo","observacoes")
    date_hierarchy = "data_partida"
    actions = ["iniciar","fechar","cancelar"]

    @admin.action(description="Iniciar viagem")
    def iniciar(self, request, qs):
        updated = qs.filter(status="PLANEJADA").update(status="EM_ANDAMENTO")
        self.message_user(request, f"{updated} viagem(ns) iniciada(s).", level=messages.SUCCESS)

    @admin.action(description="Fechar viagem")
    def fechar(self, request, qs):
        from django.utils import timezone
        fechadas = 0
        with transaction.atomic():
            for v in qs:
                if v.status in ("PLANEJADA","EM_ANDAMENTO"):
                    if not v.data_retorno: v.data_retorno = timezone.now()
                    v.status = "FECHADA"
                    v.full_clean(); v.save()
                    fechadas += 1
        self.message_user(request, f"{fechadas} viagem(ns) fechada(s).", level=messages.SUCCESS)

    @admin.action(description="Cancelar viagem")
    def cancelar(self, request, qs):
        updated = qs.exclude(status="FECHADA").update(status="CANCELADA")
        self.message_user(request, f"{updated} viagem(ns) cancelada(s).", level=messages.WARNING)
