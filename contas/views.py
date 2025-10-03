from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .forms import RegistroForm
from .decorators import admin_required

def registrar(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Conta criada com sucesso! Faça login.")
            return redirect("contas:login")
        else:
            messages.error(request, "Corrija os erros abaixo.")
    else:
        form = RegistroForm()
    return render(request, "contas/registrar.html", {"form": form})

@login_required(login_url="contas:login")
def dashboard(request):
    return render(request, "contas/dashboard.html")

@admin_required
def admin_area(request):
    return render(request, "contas/admin_area.html")

def error_403(request, exception=None):
    return render(request, "403.html", status=403)
