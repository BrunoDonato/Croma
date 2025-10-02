from django.contrib import messages
from django.shortcuts import render, redirect

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