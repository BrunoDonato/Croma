from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.http import HttpResponse

from django.db.models import Sum, F, Q
from django.db.models.functions import Coalesce
from django.contrib import messages

import csv

from .models import Produto, SaldoEstoque, Loja, Categoria, Movimentacao
from contas.views import is_admin


# Listagem do Estoque
@login_required
@user_passes_test(is_admin)
def estoque_home(request):
    # Base de produtos
    base_qs = Produto.objects.select_related("categoria")

    # Anota saldo do Central e total geral (todas as lojas)
    qs_anotado = base_qs.annotate(
        saldo_central=Coalesce(
            Sum(
                "saldos__quantidade",
                filter=Q(saldos__loja__is_central=True),
            ),
            0,
        ),
        total_geral=Coalesce(
            Sum("saldos__quantidade"),
            0,
        ),
    )

    # Filtros da Tela
    categoria_id = (request.GET.get("categoria") or "").strip()
    ativo = (request.GET.get("ativo") or "").strip()  # "", "sim", "nao"
    situacao = (request.GET.get("situacao_central") or "").strip()  # "", "abaixo", "ok", "zerado"

    qs = qs_anotado

    if categoria_id:
        qs = qs.filter(categoria_id=categoria_id)

    if ativo == "sim":
        qs = qs.filter(ativo=True)
    elif ativo == "nao":
        qs = qs.filter(ativo=False)

    # Situação em relação ao Central
    if situacao == "abaixo":
        qs = qs.filter(saldo_central__lt=F("estoque_minimo"))
    elif situacao == "ok":
        qs = qs.filter(saldo_central__gte=F("estoque_minimo"), saldo_central__gt=0)
    elif situacao == "zerado":
        qs = qs.filter(saldo_central=0)

    # Limite de segurança na tela
    produtos = qs.order_by("nome")[:200]

    # COMBOS DE FILTRO
    categorias = Categoria.objects.all().order_by("nome")

    # KPIs DOS CARDS
    # Itens cadastrados
    kpi_itens = base_qs.count()

    # Itens ativos
    kpi_ativos = base_qs.filter(ativo=True).count()

    # Produtos abaixo do mínimo (Central) em toda a base
    kpi_abaixo_min = qs_anotado.filter(saldo_central__lt=F("estoque_minimo")).count()

    # Produtos com Central zerado
    kpi_central_zerado = qs_anotado.filter(saldo_central=0).count()

    # Total geral de itens (somando saldos de todas as lojas)
    kpi_total_geral = SaldoEstoque.objects.aggregate(
        total=Coalesce(Sum("quantidade"), 0)
    )["total"]

    context = {
        "produtos": produtos,
        "categorias": categorias,

        "filtro_categoria": categoria_id,
        "filtro_ativo": ativo,
        "filtro_situacao": situacao,

        # KPIs nos cards
        "kpi_itens": kpi_itens,
        "kpi_ativos": kpi_ativos,
        "kpi_abaixo_min": kpi_abaixo_min,
        "kpi_central_zerado": kpi_central_zerado,
        "kpi_total_geral": kpi_total_geral,
    }
    return render(request, "estoque/index.html", context)


# Exportação em CSV respeitando os filtros
@login_required
@user_passes_test(is_admin)
def estoque_exportar_csv(request):
    base_qs = Produto.objects.select_related("categoria")

    qs = base_qs.annotate(
        saldo_central=Coalesce(
            Sum(
                "saldos__quantidade",
                filter=Q(saldos__loja__is_central=True),
            ),
            0,
        ),
        total_geral=Coalesce(
            Sum("saldos__quantidade"),
            0,
        ),
    )

    # Mesmos filtros da tela
    categoria_id = (request.GET.get("categoria") or "").strip()
    ativo = (request.GET.get("ativo") or "").strip()  # "", "sim", "nao"
    situacao = (request.GET.get("situacao_central") or "").strip()  # "", "abaixo", "ok", "zerado"

    if categoria_id:
        qs = qs.filter(categoria_id=categoria_id)

    if ativo == "sim":
        qs = qs.filter(ativo=True)
    elif ativo == "nao":
        qs = qs.filter(ativo=False)

    if situacao == "abaixo":
        qs = qs.filter(saldo_central__lt=F("estoque_minimo"))
    elif situacao == "ok":
        qs = qs.filter(saldo_central__gte=F("estoque_minimo"), saldo_central__gt=0)
    elif situacao == "zerado":
        qs = qs.filter(saldo_central=0)

    qs = qs.order_by("nome")

    # Nome do arquivo
    partes = ["estoque"]

    if categoria_id:
        try:
            cat_nome = Categoria.objects.get(pk=categoria_id).nome
            partes.append(cat_nome.replace(" ", "_"))
        except Categoria.DoesNotExist:
            partes.append(f"cat_{categoria_id}")

    if ativo == "sim":
        partes.append("ativos")
    elif ativo == "nao":
        partes.append("inativos")

    if situacao:
        partes.append(situacao)

    fname = "_".join(partes).replace("__", "_").lower() + ".csv"

    # Response CSV
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{fname}"'
    response.write("\ufeff")  # BOM UTF-8 para Excel
    w = csv.writer(response, lineterminator="\n")

    # Cabeçalho
    w.writerow(["RELATÓRIO DE ESTOQUE"])
    from django.utils import timezone
    w.writerow(["Gerado em", timezone.now().strftime("%Y-%m-%d %H:%M")])
    w.writerow([])

    # Colunas
    w.writerow([
        "ID", "Nome", "Categoria", "Unidade",
        "Saldo no Central", "Saldo mínimo (Central)",
        "Total (todas as lojas)",
        "Fabricante", "Modelo", "Ativo",
    ])

    for p in qs:
        w.writerow([
            p.id,
            p.nome,
            p.categoria.nome if p.categoria_id else "",
            p.unidade or "",
            p.saldo_central or 0,
            p.estoque_minimo,
            p.total_geral or 0,
            p.fabricante or "",
            p.modelo or "",
            "Sim" if p.ativo else "Não",
        ])

    return response

@login_required
@user_passes_test(is_admin)
def movimentacao_form(request):

    produtos = Produto.objects.filter(ativo=True).order_by("nome")
    lojas = Loja.objects.order_by("nome")

    if request.method == "POST":
        tipo = request.POST.get("tipo")
        produto_id = request.POST.get("produto")
        origem_id = request.POST.get("origem")
        destino_id = request.POST.get("destino")
        qtd = int(request.POST.get("quantidade"))
        observacao = request.POST.get("observacao")

        try:
            produto = Produto.objects.get(id=produto_id)
        except Produto.DoesNotExist:
            messages.error(request, "Produto inválido.")
            return redirect("estoque:movimentar")

        origem = Loja.objects.filter(id=origem_id).first() if origem_id else None
        destino = Loja.objects.filter(id=destino_id).first() if destino_id else None

        # Buscar/Criar Saldos
        def get_saldo(prod, loja):
            saldo, created = SaldoEstoque.objects.get_or_create(produto=prod, loja=loja)
            return saldo

        # Entrada
        if tipo == "ENTRADA":
            saldo = get_saldo(produto, destino)
            saldo.quantidade += qtd
            saldo.save()

            Movimentacao.objects.create(
                tipo="ENTRADA",
                produto=produto,
                destino=destino,
                quantidade=qtd,
                usuario=request.user,
                observacao=observacao
            )

            messages.success(request, "Entrada registrada com sucesso!")
            return redirect("estoque:home")

        # Saída
        if tipo == "SAIDA":
            saldo = get_saldo(produto, origem)

            if saldo.quantidade < qtd:
                messages.error(request, "Quantidade insuficiente para saída.")
                return redirect("estoque:movimentar")

            saldo.quantidade -= qtd
            saldo.save()

            Movimentacao.objects.create(
                tipo="SAIDA",
                produto=produto,
                origem=origem,
                quantidade=qtd,
                usuario=request.user,
                observacao=observacao
            )

            messages.success(request, "Saída registrada com sucesso!")
            return redirect("estoque:home")

        # Transferência
        if tipo == "TRANSFERENCIA":
            if origem == destino:
                messages.error(request, "Origem e destino não podem ser iguais.")
                return redirect("estoque:movimentar")

            saldo_origem = get_saldo(produto, origem)
            saldo_destino = get_saldo(produto, destino)

            if saldo_origem.quantidade < qtd:
                messages.error(request, "Saldo insuficiente para transferência.")
                return redirect("estoque:movimentar")

            saldo_origem.quantidade -= qtd
            saldo_destino.quantidade += qtd
            saldo_origem.save()
            saldo_destino.save()

            Movimentacao.objects.create(
                tipo="TRANSFERENCIA",
                produto=produto,
                origem=origem,
                destino=destino,
                quantidade=qtd,
                usuario=request.user,
                observacao=observacao
            )

            messages.success(request, "Transferência realizada com sucesso!")
            return redirect("estoque:home")

    context = {
        "produtos": produtos,
        "lojas": lojas,
    }
    return render(request, "estoque/movimentacao_form.html", context)