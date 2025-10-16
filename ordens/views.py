from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from .forms import OrdemServicoForm

@login_required
def criar_os(request):
    if not request.user.is_superuser:
        if not hasattr(request.user, "perfil") or not request.user.perfil or not request.user.perfil.loja_id:
            messages.error(request, "Seu usuário não está vinculado a uma loja. Contate o administrador.")
            return redirect(reverse("ordens:os_sucesso"))
    if request.method == "POST":
        form = OrdemServicoForm(request.POST, user=request.user)
        if form.is_valid():
            os_obj = form.save(commit=False)
            os_obj.solicitante = request.user
            os_obj.save()
            return redirect(reverse("ordens:os_sucesso"))
    else:
        form = OrdemServicoForm(user=request.user)
    return render(request, "ordens/os_criar.html", {"form": form})

@login_required
def os_sucesso(request):
    return render(request, "ordens/os_sucesso.html")
