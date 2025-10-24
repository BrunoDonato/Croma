from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.core.exceptions import PermissionDenied

from .forms import (
    OrdemServicoForm,
    AndamentoForm,
    AnexoForm,
    FinalizarForm,
    CancelarForm,
    AtribuirTecnicoForm,
)
from .models import OrdemServico


from contas.views import is_admin


# Criar OS (Usuário comum ou admin)
@login_required
def criar_os(request):
    if not request.user.is_superuser:
        if not hasattr(request.user, "perfil") or not getattr(request.user.perfil, "loja_id", None):
            messages.error(request, "Seu usuário não está vinculado a uma loja. Contate o administrador.")
            return redirect(reverse("ordens:os_sucesso"))

    if request.method == "POST":
        form = OrdemServicoForm(request.POST, user=request.user)
        if form.is_valid():
            os_obj = form.save(commit=False)
            os_obj.solicitante = request.user
            os_obj.save()
            messages.success(request, "Ordem de Serviço registrada com sucesso.")
            return redirect(reverse("ordens:os_sucesso"))
    else:
        form = OrdemServicoForm(user=request.user)

    return render(request, "ordens/os_criar.html", {"form": form})


@login_required
def os_sucesso(request):
    return render(request, "ordens/os_sucesso.html")


# LISTAGENS

# Listagem global das OS (apenas admin)
@login_required
@user_passes_test(is_admin)
def listar_os(request):
    ordens = OrdemServico.objects.select_related("loja", "solicitante", "tecnico_responsavel").order_by("-data_abertura")
    return render(request, "ordens/os_listar.html", {"ordens": ordens})


# Minhas solicitações (usuário comum)
@login_required
def os_minhas(request):
    ordens = (
        OrdemServico.objects
        .filter(solicitante=request.user)
        .select_related("loja")
        .order_by("-data_abertura")
    )
    return render(
        request,
        "ordens/os_listar.html",
        {
            "ordens": ordens,
            "page_title": "Minhas Ordens de Serviço",
            "page_subtitle": "Acompanhe as solicitações que você abriu.",
            "is_my_list": True,
        },
    )

# Detalhe
@login_required
def detalhe_os(request, pk):
    os_obj = get_object_or_404(
        OrdemServico.objects.select_related("loja", "solicitante"),
        pk=pk
    )

    # Permissão: admin, solicitante ou técnico
    if not (is_admin(request.user) or os_obj.solicitante == request.user or os_obj.tecnico_responsavel == request.user):
        raise PermissionDenied()

    is_admin_flag = is_admin(request.user)

    # Form de andamento: esconde "visibilidade" para usuário comum
    andamento_form = AndamentoForm()
    if not is_admin_flag:
        andamento_form.fields.pop("visibilidade", None)

    # Apenas públicos para não-admin (e que não seja o técnico responsável)
    andamentos_qs = os_obj.andamentos.all()
    if not is_admin_flag and request.user != os_obj.tecnico_responsavel:
        andamentos_qs = andamentos_qs.filter(visibilidade="PUBLICO")

    context = {
        "os": os_obj,
        "andamento_form": AndamentoForm(),
        "anexo_form": AnexoForm(),
        "finalizar_form": FinalizarForm(instance=os_obj),
        "cancelar_form": CancelarForm(instance=os_obj),
        "atribuir_form": AtribuirTecnicoForm(instance=os_obj),
        "is_admin": is_admin(request.user),
        "andamentos": andamentos_qs,
    }
    return render(request, "ordens/os_detalhe.html", context)


# Comentarios/andamentos
@login_required
def os_comentario(request, pk):
    os_obj = get_object_or_404(OrdemServico, pk=pk)
    if not (is_admin(request.user) or os_obj.solicitante == request.user or os_obj.tecnico_responsavel == request.user):
        raise PermissionDenied()

    if request.method == "POST":
        form = AndamentoForm(request.POST)
        if form.is_valid():
            andamento = form.save(commit=False)
            andamento.os = os_obj
            andamento.autor = request.user
            if not is_admin(request.user):     # ✅ força público
                andamento.visibilidade = "PUBLICO"
            andamento.save()
            messages.success(request, "Comentário registrado com sucesso.")
    return redirect("ordens:os_detalhe", pk=pk)


# Anexos
@login_required
def os_anexo(request, pk):
    os_obj = get_object_or_404(OrdemServico, pk=pk)
    if not (is_admin(request.user) or os_obj.solicitante == request.user or os_obj.tecnico_responsavel == request.user):
        raise PermissionDenied()

    if request.method == "POST":
        form = AnexoForm(request.POST, request.FILES)
        if form.is_valid():
            anexo = form.save(commit=False)
            anexo.os = os_obj
            anexo.enviado_por = request.user
            anexo.save()
            messages.success(request, "Anexo enviado com sucesso.")
    return redirect("ordens:os_detalhe", pk=pk)



# (analisar/executar/finalizar/cancelar)
@login_required
def os_acao_status(request, pk):
    os_obj = get_object_or_404(OrdemServico, pk=pk)
    if not (is_admin(request.user) or os_obj.tecnico_responsavel == request.user):
        raise PermissionDenied()

    acao = request.POST.get("acao")

    if acao == "EM_ANALISE":
        try:
            os_obj.mudar_status("EM_ANALISE", autor=request.user, texto_andamento="Início da análise", visibilidade="INTERNO")
            messages.success(request, "OS marcada como 'Em análise'.")
        except Exception as e:
            messages.error(request, str(e))

    elif acao == "EM_EXECUCAO":
        try:
            os_obj.mudar_status("EM_EXECUCAO", autor=request.user, texto_andamento="Início da execução", visibilidade="INTERNO")
            messages.success(request, "OS marcada como 'Em execução'.")
        except Exception as e:
            messages.error(request, str(e))

    elif acao == "FINALIZADA":
        form = FinalizarForm(request.POST, instance=os_obj)
        if form.is_valid():
            form.save()
            try:
                os_obj.mudar_status("FINALIZADA", autor=request.user, texto_andamento="Finalizada", visibilidade="PUBLICO")
                messages.success(request, "OS finalizada com sucesso.")
            except Exception as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Informe a solução para finalizar a OS.")

    elif acao == "CANCELADA":
        form = CancelarForm(request.POST, instance=os_obj)
        if form.is_valid():
            form.save()
            try:
                os_obj.mudar_status("CANCELADA", autor=request.user, texto_andamento="Cancelada", visibilidade="INTERNO")
                messages.success(request, "OS cancelada com sucesso.")
            except Exception as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Informe o motivo do cancelamento.")

    else:
        messages.error(request, "Ação inválida ou não permitida.")

    return redirect("ordens:os_detalhe", pk=pk)


# Atribuir tecnico (admin)
@login_required
@user_passes_test(is_admin)
def os_atribuir(request, pk):
    os_obj = get_object_or_404(OrdemServico, pk=pk)

    if request.method == "POST":
        form = AtribuirTecnicoForm(request.POST, instance=os_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Técnico/prioridade atualizados.")
    return redirect("ordens:os_detalhe", pk=pk)
