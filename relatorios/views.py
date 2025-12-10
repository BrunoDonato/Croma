from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.db.models import Count, F, Avg, DurationField, ExpressionWrapper
from django.db.models.functions import TruncMonth
from django.http import HttpResponse

import csv
from datetime import datetime

from viagens.models import Viagem
from ordens.models import OrdemServico
from contas.views import is_admin

from django.utils import timezone
from estoque.models import Loja


# Helper aplica filtros da tela (OS)
def _filtrar_os(request, qs):
    status = (request.GET.get("status") or "").strip()
    loja_id = (request.GET.get("loja") or "").strip()
    dt_ini = (request.GET.get("dt_ini") or "").strip()
    dt_fim = (request.GET.get("dt_fim") or "").strip()

    if status:
        qs = qs.filter(status=status)
    if loja_id:
        qs = qs.filter(loja_id=loja_id)
    if dt_ini:
        qs = qs.filter(data_abertura__date__gte=dt_ini)
    if dt_fim:
        qs = qs.filter(data_abertura__date__lte=dt_fim)
    return qs


# Helper aplica filtros da tela VIAGENS. Filtros: origem, destino, responsavel, status, dt_ini, dt_fim
def _filtrar_viagens(request, qs):
    origem_id = (request.GET.get("origem") or "").strip()
    destino_id = (request.GET.get("destino") or "").strip()
    responsavel_id = (request.GET.get("responsavel") or "").strip()
    status = (request.GET.get("status") or "").strip()
    dt_ini = (request.GET.get("dt_ini") or "").strip()
    dt_fim = (request.GET.get("dt_fim") or "").strip()

    if origem_id:
        qs = qs.filter(origem_id=origem_id)
    if destino_id:
        qs = qs.filter(destino_id=destino_id)
    if responsavel_id:
        qs = qs.filter(responsavel_id=responsavel_id)
    if status:
        qs = qs.filter(status=status)
    if dt_ini:
        qs = qs.filter(data_partida__date__gte=dt_ini)
    if dt_fim:
        qs = qs.filter(data_partida__date__lte=dt_fim)
    return qs


# Relatorios de viagens
@login_required
@user_passes_test(is_admin)
def relatorio_viagens(request):
    qs_base = (
        Viagem.objects
        .select_related("origem", "destino", "responsavel")
        .order_by("-data_partida")
    )
    qs = _filtrar_viagens(request, qs_base)

    viagens_por_loja = (
        qs.values(nome=F("destino__nome"))
          .annotate(qtd=Count("id"))
          .order_by("-qtd")
    )
    viagens_por_mes = (
        qs.annotate(mes=TruncMonth("data_partida"))
          .values("mes")
          .annotate(qtd=Count("id"))
          .order_by("mes")
    )

    total_viagens = qs.count()
    dist_status = list(qs.values("status").annotate(qtd=Count("id")).order_by("-qtd"))
    top_responsaveis = list(qs.values(nome=F("responsavel__username")).annotate(qtd=Count("id")).order_by("-qtd")[:5])

    # tabela
    viagens = qs[:200]

    # combos
    lojas = Loja.objects.order_by("nome")
    responsaveis = (
        qs_base.values("responsavel_id", "responsavel__username")
               .distinct()
               .order_by("responsavel__username")
    )
    status_distintos = qs_base.values_list("status", flat=True).distinct().order_by()

    return render(request, "relatorios/viagens.html", {
        # Converte para list
        "viagens_por_loja": list(viagens_por_loja),
        "viagens_por_mes": list(viagens_por_mes),

        "total_viagens": total_viagens,
        "dist_status": dist_status,
        "top_responsaveis": top_responsaveis,

        "viagens": viagens,
        "lojas": lojas,
        "responsaveis": list(responsaveis),
        "status_distintos": list(status_distintos),
    })


# Relatorios de OS
@login_required
@user_passes_test(is_admin)
def rel_os(request):
    qs_base = (
        OrdemServico.objects
        .select_related("loja", "solicitante", "tecnico_responsavel")
        .order_by("-data_abertura")
    )
    qs = _filtrar_os(request, qs_base)

    # Gráfico OS por prioridade (filtrado)
    dist_prio = (
        qs.values("prioridade")
          .annotate(total=Count("id"))
          .order_by()
    )
    prio_labels = [d["prioridade"] for d in dist_prio]
    prio_values = [d["total"] for d in dist_prio]

    # Gráfico lojas com mais OS em aberto (filtrado)
    dist_loja_abertas = (
        qs.filter(status__in=["ABERTA", "EM_ANALISE", "EM_EXECUCAO"])
          .values("loja__nome")
          .annotate(total=Count("id"))
          .order_by("-total")[:5]
    )
    top_lojas_labels = [d["loja__nome"] for d in dist_loja_abertas]
    top_lojas_values = [d["total"] for d in dist_loja_abertas]

    # Tabela (filtrada)
    ordens = qs[:200]

    context = {
        # Tabela
        "ordens": ordens,
        "qs": ordens,

        # Prioridade
        "prio_labels": prio_labels,
        "prio_values": prio_values,
        "chart_prio_labels": prio_labels,
        "chart_prio_values": prio_values,

        # Top lojas
        "top_lojas_labels": top_lojas_labels,
        "top_lojas_values": top_lojas_values,
        "chart_lojas_labels": top_lojas_labels,
        "chart_lojas_values": top_lojas_values,

        # Para os filtros do template
        "status_choices": OrdemServico.STATUS_CHOICES,
        "lojas": Loja.objects.all().order_by("nome"),
    }

    return render(request, "relatorios/os.html", context)


@login_required
@user_passes_test(is_admin)
def rel_os_csv(request):
    qs_base = (
        OrdemServico.objects
        .select_related("loja", "solicitante", "tecnico_responsavel", "categoria")
        .order_by("id")
    )
    qs = _filtrar_os(request, qs_base)

    # Nome dinâmico do arquivo CSV
    loja_id = (request.GET.get("loja") or "").strip()
    status = (request.GET.get("status") or "").strip()
    dt_ini = (request.GET.get("dt_ini") or "").strip()
    dt_fim = (request.GET.get("dt_fim") or "").strip()

    partes_nome = ["relatorio_os"]
    if loja_id:
        try:
            loja_nome = Loja.objects.get(pk=loja_id).nome
            partes_nome.append(loja_nome.replace(" ", "_"))
        except Loja.DoesNotExist:
            partes_nome.append(f"loja_{loja_id}")
    if status:
        partes_nome.append(status.lower())
    if dt_ini and dt_fim:
        partes_nome.append(f"{dt_ini}_a_{dt_fim}")
    elif dt_ini:
        partes_nome.append(f"desde_{dt_ini}")
    elif dt_fim:
        partes_nome.append(f"ate_{dt_fim}")

    fname = "_".join(partes_nome).replace("__", "_").lower() + ".csv"

    # Response UTF-8 BOM
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{fname}"'
    response.write("\ufeff")
    w = csv.writer(response, lineterminator="\n")

    # Agregados respeitando filtros
    total_os = qs.count()

    dist_status = (
        qs.values("status")
          .annotate(qtd=Count("id"))
          .order_by()
    )
    dist_prio = (
        qs.values("prioridade")
          .annotate(qtd=Count("id"))
          .order_by()
    )
    dist_loja_abertas = (
        qs.filter(status__in=["ABERTA", "EM_ANALISE", "EM_EXECUCAO"])
          .values("loja__nome")
          .annotate(qtd=Count("id"))
          .order_by("-qtd")[:5]
    )

    delta = ExpressionWrapper(F("data_fechamento") - F("data_abertura"), output_field=DurationField())
    mttr_qs = (
        qs.filter(status="FINALIZADA", data_fechamento__isnull=False)
          .annotate(delta=delta)
          .aggregate(media=Avg("delta"))
    )
    mttr_horas = round((mttr_qs["media"].total_seconds() / 3600), 1) if mttr_qs["media"] else None

    # Cabeçalho
    w.writerow(["RELATÓRIO DE ORDENS DE SERVIÇO"])
    w.writerow(["Gerado em", timezone.now().strftime("%Y-%m-%d %H:%M")])

    if any([loja_id, status, dt_ini, dt_fim]):
        w.writerow([])
        w.writerow(["FILTROS APLICADOS"])
        if loja_id:
            try:
                w.writerow(["Loja", Loja.objects.get(pk=loja_id).nome])
            except Loja.DoesNotExist:
                w.writerow(["Loja", loja_id])
        if status:
            w.writerow(["Status", dict(OrdemServico.STATUS_CHOICES).get(status, status)])
        if dt_ini:
            w.writerow(["Data inicial", dt_ini])
        if dt_fim:
            w.writerow(["Data final", dt_fim])

    w.writerow([])

    # Resumo geral
    w.writerow(["RESUMO"])
    w.writerow(["Total de OS", total_os])
    w.writerow(["MTTR médio (horas)", mttr_horas if mttr_horas is not None else "—"])
    w.writerow([])

    # Distribuições e detalhes
    w.writerow(["DISTRIBUIÇÃO POR STATUS"])
    w.writerow(["Status", "Quantidade"])
    for d in dist_status:
        w.writerow([dict(OrdemServico.STATUS_CHOICES).get(d["status"], d["status"]), d["qtd"]])
    w.writerow([])

    w.writerow(["DISTRIBUIÇÃO POR PRIORIDADE"])
    w.writerow(["Prioridade", "Quantidade"])
    for d in dist_prio:
        w.writerow([dict(OrdemServico.PRIORIDADE_CHOICES).get(d["prioridade"], d["prioridade"]), d["qtd"]])
    w.writerow([])

    w.writerow(["LOJAS COM MAIS OS EM ABERTO"])
    w.writerow(["Loja", "Quantidade"])
    for d in dist_loja_abertas:
        w.writerow([d["loja__nome"] or "", d["qtd"]])
    w.writerow([])

    # Detalhe linha a linha
    w.writerow(["DETALHES OS"])
    w.writerow([
        "ID", "Loja", "Solicitante", "Técnico Responsável",
        "Status", "Prioridade", "Data Abertura", "Data Fechamento",
        "Categoria", "Custo Total (R$)"
    ])
    for os in qs:
        w.writerow([
            os.id,
            os.loja.nome if os.loja_id else "",
            os.solicitante.username if os.solicitante_id else "",
            os.tecnico_responsavel.username if os.tecnico_responsavel_id else "",
            os.get_status_display(),
            os.get_prioridade_display(),
            os.data_abertura.strftime("%Y-%m-%d %H:%M"),
            os.data_fechamento.strftime("%Y-%m-%d %H:%M") if os.data_fechamento else "",
            getattr(os.categoria, "nome", "") if hasattr(os, "categoria") and os.categoria_id else "",
            f"{os.custo_total:.2f}" if os.custo_total is not None else "",
        ])

    return response


@login_required
@user_passes_test(is_admin)
def rel_os_pdf(request):
    # Placeholder
    return HttpResponse("Exportação PDF ainda não implementada.", content_type="text/plain")


# Relatório de Problemas
@login_required
@user_passes_test(is_admin)
def rel_problemas(request):
    qs = (
        OrdemServico.objects
        .select_related("loja", "solicitante", "tecnico_responsavel", "categoria")
        .order_by("-data_abertura")
    )

    # Filtros
    loja_id = request.GET.get("loja") or ""
    dt_ini = request.GET.get("dt_ini") or ""
    dt_fim = request.GET.get("dt_fim") or ""

    if loja_id:
        qs = qs.filter(loja_id=loja_id)

    def _parse_date(d: str):
        try:
            return datetime.strptime(d, "%Y-%m-%d").date()
        except Exception:
            return None

    d_ini = _parse_date(dt_ini)
    d_fim = _parse_date(dt_fim)

    if d_ini:
        qs = qs.filter(data_abertura__date__gte=d_ini)
    if d_fim:
        qs = qs.filter(data_abertura__date__lte=d_fim)

    # Distribuição por categoria
    dist_cat = (
        qs.filter(categoria__isnull=False)
          .values("categoria__nome")
          .annotate(total=Count("id"))
          .order_by("-total")[:10]
    )
    cat_labels = [d["categoria__nome"] for d in dist_cat]
    cat_values = [d["total"] for d in dist_cat]

    # MTTR por categoria (média em horas), apenas finalizadas
    delta = ExpressionWrapper(
        F("data_fechamento") - F("data_abertura"),
        output_field=DurationField()
    )
    mttr_qs = (
        qs.filter(status="FINALIZADA", categoria__isnull=False, data_fechamento__isnull=False)
          .annotate(delta=delta)
          .values("categoria__nome")
          .annotate(mttr=Avg("delta"))
          .order_by("categoria__nome")
    )

    def td_to_hours(td):
        if td is None:
            return 0.0
        return round(td.total_seconds() / 3600, 1)

    mttr_labels = [d["categoria__nome"] for d in mttr_qs]
    mttr_values = [td_to_hours(d["mttr"]) for d in mttr_qs]

    lojas = (qs.model._meta.get_field("loja").remote_field.model
             .objects.order_by("nome"))

    return render(request, "relatorios/problemas.html", {
        "ordens": qs[:200],
        "lojas": lojas,
        "cat_labels": cat_labels,
        "cat_values": cat_values,
        "mttr_labels": mttr_labels,
        "mttr_values": mttr_values,
    })


@login_required
@user_passes_test(is_admin)
def rel_problemas_csv(request):
    qs = (
        OrdemServico.objects
        .select_related("loja", "solicitante", "tecnico_responsavel", "categoria")
        .order_by("id")
    )

    total_os = qs.count()

    # Top categorias
    dist_cat = (
        qs.filter(categoria__isnull=False)
          .values("categoria__nome")
          .annotate(qtd=Count("id"))
          .order_by("-qtd")[:15]
    )

    # MTTR por categoria (horas)
    delta = ExpressionWrapper(F("data_fechamento") - F("data_abertura"), output_field=DurationField())
    mttr_cat = (
        qs.filter(status="FINALIZADA", categoria__isnull=False, data_fechamento__isnull=False)
          .annotate(delta=delta)
          .values("categoria__nome")
          .annotate(mttr=Avg("delta"))
          .order_by("categoria__nome")
    )

    # Response UTF-8 com BOM para Excel
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="relatorio_problemas_completo.csv"'
    response.write("\ufeff")  # BOM UTF-8
    w = csv.writer(response, lineterminator="\n")

    # Cabeçalho
    w.writerow(["RELATORIO DE PROBLEMAS"])
    w.writerow(["Gerado em", timezone.now().strftime("%Y-%m-%d %H:%M")])
    w.writerow(["Total de OS consideradas", total_os])
    w.writerow([])

    # Top categorias
    w.writerow(["TOP CATEGORIAS (Por quantidade)"])
    w.writerow(["Categoria", "Quantidade"])
    for d in dist_cat:
        w.writerow([d["categoria__nome"], d["qtd"]])
    w.writerow([])

    # MTTR por categoria
    w.writerow(["MTTR POR CATEGORIA (Em horas, apenas para OS finalizadas)"])
    w.writerow(["Categoria", "MTTR (h)"])
    for d in mttr_cat:
        horas = round(d["mttr"].total_seconds() / 3600, 1) if d["mttr"] else 0.0
        w.writerow([d["categoria__nome"], horas])
    w.writerow([])

    # Detalhe
    w.writerow(["DETALHES OS"])
    w.writerow([
        "ID", "Loja", "Solicitante", "Técnico Responsável",
        "Status", "Prioridade", "Data Abertura", "Data Fechamento",
        "Categoria"
    ])
    for os in qs:
        w.writerow([
            os.id,
            os.loja.nome if os.loja_id else "",
            os.solicitante.username if os.solicitante_id else "",
            os.tecnico_responsavel.username if os.tecnico_responsavel_id else "",
            os.get_status_display(),
            os.get_prioridade_display(),
            os.data_abertura.strftime("%Y-%m-%d %H:%M"),
            os.data_fechamento.strftime("%Y-%m-%d %H:%M") if os.data_fechamento else "",
            getattr(os.categoria, "nome", "") if hasattr(os, "categoria") and os.categoria_id else "",
        ])

    return response
