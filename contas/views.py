from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import RegistroForm, LoginForm

def registrar(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()  # cria o usuário
            messages.success(request, "Conta criada com sucesso! Faça login.")
            return redirect("contas:login")
        else:
            messages.error(request, "Corrija os erros abaixo.")
    else:
        form = RegistroForm()
    return render(request, "contas/registrar.html", {"form": form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect("contas:dashboard")

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Bem-vindo, {user.username}!")
            return redirect("contas:dashboard")
        else:
            messages.error(request, "Usuário ou senha inválidos.")
    else:
        form = LoginForm()
    return render(request, "contas/login.html", {"form": form})

def logout_view(request):
    logout(request)
    messages.info(request, "Você saiu da sua conta.")
    return redirect("contas:login")

@login_required
def dashboard(request):
    return render(request, "contas/dashboard.html")
