from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .forms import RegistroForm

#Cadastro de usuário
def registrar(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()  # Cria o usuário com senha hasheada
            messages.success(request, "Conta criada com sucesso! Faça login.")
            return redirect("contas:login")
        else:
            messages.error(request, "Corrija os erros abaixo.")
    else:
        form = RegistroForm()
    return render(request, "contas/registrar.html", {"form": form})

# Pagina de destino após logar
def dashboard(request):
    return render(request, "contas/dashboard.html")

def is_admin(user):
    return user.is_superuser or user.groups.filter(name="admin").exists()

@login_required
def admin_area(request):
    if not is_admin(request.user):
        raise PermissionDenied
    return render(request, "contas/admin_area.html")

def error_403(request, exception=None):
    return render(request, "403.html", status=403)
