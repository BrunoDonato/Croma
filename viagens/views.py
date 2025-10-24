from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from contas.views import is_admin
from ordens.models import OrdemServico
from .forms import ViagemForm
from .models import Viagem

# Criar Viagem (apenas Admin)
@login_required
@user_passes_test(is_admin)
def criar_viagem(request, os_id=None):
    # Descobre a OS de referência
    os_arg = os_id or request.GET.get("os")
    os_ref = None
    if os_arg:
        try:
            os_ref = OrdemServico.objects.select_related("loja").get(pk=int(os_arg))
        except (ValueError, OrdemServico.DoesNotExist):
            os_ref = None

    # Initial quando já sei a OS/loja de destino
    initial = {}
    if os_ref:
        initial["referencia_os"] = os_ref
        initial["destino"] = os_ref.loja_id

    if request.method == "POST":
        form = ViagemForm(request.POST, user=request.user, os_id=os_arg, initial=initial)
        if form.is_valid():
            viagem = form.save()
            messages.success(request, "Viagem cadastrada com sucesso.")
            return redirect("viagens:viagem_detalhe", pk=viagem.pk)
    else:
        form = ViagemForm(user=request.user, os_id=os_arg, initial=initial)

    return render(request, "viagens/viagem_nova.html", {"form": form, "os_ref": os_ref})


# Detalhes da Viagem (apenas Admin)
@login_required
@user_passes_test(is_admin)
def detalhe_viagem(request, pk: int):
    v = get_object_or_404(
        Viagem.objects.select_related(
            "referencia_os",
            "origem",
            "destino",
            "responsavel",
            "veiculo",
        ),
        pk=pk,
    )
    return render(request, "viagens/viagem_detalhe.html", {"v": v})
