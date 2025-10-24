from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.db.models import Count, F
from django.db.models.functions import TruncMonth

from viagens.models import Viagem
from contas.views import is_admin

@login_required
@user_passes_test(is_admin)
def relatorio_viagens(request):
    viagens_por_loja = (
        Viagem.objects
        .values(nome=F("destino__nome"))
        .annotate(qtd=Count("id"))
        .order_by("-qtd")
    )

    viagens_por_mes = (
        Viagem.objects
        .annotate(mes=TruncMonth("data_partida"))
        .values("mes")
        .annotate(qtd=Count("id"))
        .order_by("mes")
    )

    return render(request, "relatorios/viagens.html", {
        "viagens_por_loja": viagens_por_loja,
        "viagens_por_mes": viagens_por_mes,
    })
