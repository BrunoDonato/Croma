import csv
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q

from estoque.models import Loja
from .models import PrestadorServico, OrdemExterna
from .forms import OrdemExternaForm


@login_required
def ordem_externa_lista(request):
    ordens = OrdemExterna.objects.select_related("loja", "prestador").all()

    status = request.GET.get("status", "")
    prioridade = request.GET.get("prioridade", "")
    prestador_id = request.GET.get("prestador", "")
    loja_id = request.GET.get("loja", "")
    busca = request.GET.get("q", "")

    if status:
        ordens = ordens.filter(status=status)

    if prioridade:
        ordens = ordens.filter(prioridade=prioridade)

    if prestador_id:
        ordens = ordens.filter(prestador_id=prestador_id)

    if loja_id:
        ordens = ordens.filter(loja_id=loja_id)

    if busca:
        ordens = ordens.filter(
            Q(equipamento__icontains=busca)
            | Q(numero_serie__icontains=busca)
            | Q(numero_os_prestador__icontains=busca)
        )

    if request.GET.get("export") == "csv":
        response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = 'attachment; filename="ordens_externas.csv"'

        writer = csv.writer(response, delimiter=";")

        writer.writerow([
            "ID",
            "Loja",
            "Prestador",
            "Equipamento",
            "Nº Série",
            "Status",
            "Prioridade",
            "Data envio",
            "Previsão retorno",
            "Data retorno",
            "Nº OS prestador",
            "Valor orçado",
            "Valor aprovado",
            "Observações",
        ])

        for o in ordens:
            writer.writerow([
                o.id,
                o.loja.nome if o.loja else "",
                o.prestador.nome if o.prestador else "",
                o.equipamento,
                o.numero_serie or "",
                o.get_status_display(),
                o.get_prioridade_display(),
                o.data_envio.strftime("%d/%m/%Y") if o.data_envio else "",
                o.data_previsao_retorno.strftime("%d/%m/%Y") if o.data_previsao_retorno else "",
                o.data_retorno.strftime("%d/%m/%Y") if o.data_retorno else "",
                o.numero_os_prestador or "",
                o.valor_orcado or "",
                o.valor_aprovado or "",
                (o.observacoes or "").replace("\n", " ").replace("\r", " "),
            ])

        return response

    context = {
        "ordens": ordens,
        "status_escolhido": status,
        "prioridade_escolhida": prioridade,
        "prestador_escolhido": prestador_id,
        "loja_escolhida": loja_id,
        "busca": busca,
        "prestadores": PrestadorServico.objects.filter(ativo=True),
        "lojas": Loja.objects.filter(ativa=True),
    }
    return render(request, "prestadores/ordem_externa_lista.html", context)


@login_required
def ordem_externa_nova(request):
    if request.method == "POST":
        form = OrdemExternaForm(request.POST)
        if form.is_valid():
            ordem = form.save(commit=False)
            ordem.criado_por = request.user
            ordem.save()
            messages.success(request, "Ordem externa criada com sucesso.")
            return redirect("prestadores:ordem_externa_lista")
    else:
        form = OrdemExternaForm()

    return render(request, "prestadores/ordem_externa_form.html", {"form": form})


@login_required
def ordem_externa_detalhe(request, pk):
    ordem = get_object_or_404(OrdemExterna, pk=pk)

    if request.method == "POST":
        form = OrdemExternaForm(request.POST, instance=ordem)
        if form.is_valid():
            form.save()
            messages.success(request, "Ordem externa atualizada com sucesso.")
            return redirect("prestadores:ordem_externa_detalhe", pk=pk)
    else:
        form = OrdemExternaForm(instance=ordem)

    return render(
        request,
        "prestadores/ordem_externa_detalhe.html",
        {"form": form, "ordem": ordem},
    )


@login_required
def contatos_lista(request):
    busca = request.GET.get("q", "")
    prestadores = PrestadorServico.objects.filter(ativo=True)

    if busca:
        prestadores = prestadores.filter(
            Q(nome__icontains=busca)
            | Q(telefone__icontains=busca)
            | Q(email__icontains=busca)
        )

    prestadores = prestadores.order_by("nome")

    return render(
        request,
        "prestadores/contatos.html",
        {"prestadores": prestadores, "busca": busca},
    )
